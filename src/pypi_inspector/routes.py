import urllib.parse

import gunicorn.http.errors
import requests
from flask import Blueprint
from flask import abort, redirect, render_template, request, url_for
from packaging.utils import canonicalize_name
from packaging.version import Version

pypi_bp = Blueprint("pypi", __name__, template_folder="templates")

# Lightweight datastore ;)
dists = {}


def parse(version: str) -> "Version":
    """Parse the given version string and return a :class:`Version` object"""
    return Version(version)

import tarfile
import zipfile
from io import BytesIO


class Distribution:
    def namelist(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError


class ZipDistribution(Distribution):
    def __init__(self, f):
        f.seek(0)
        self.zipfile = zipfile.ZipFile(f)

    def namelist(self):
        return [i.filename for i in self.zipfile.infolist() if not i.is_dir()]

    def contents(self, filepath):
        try:
            return self.zipfile.read(filepath).decode()
        except KeyError:
            raise FileNotFoundError


class TarGzDistribution(Distribution):
    def __init__(self, f):
        f.seek(0)
        self.tarfile = tarfile.open(fileobj=f, mode="r:gz")

    def namelist(self):
        return [i.name for i in self.tarfile.getmembers() if not i.isdir()]

    def contents(self, filepath):
        try:
            file_ = self.tarfile.extractfile(filepath)
            if file_:
                return file_.read().decode()
            else:
                raise FileNotFoundError
        except KeyError:
            raise FileNotFoundError


def _get_dist(first, second, rest, distname):
    if distname in dists:
        return dists[distname]

    url = f"https://files.pythonhosted.org/packages/{first}/{second}/{rest}/{distname}"
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        abort(exc.response.status_code)

    f = BytesIO(resp.content)

    if (
        distname.endswith(".whl")
        or distname.endswith(".zip")
        or distname.endswith(".egg")
    ):
        distfile = ZipDistribution(f)
        dists[distname] = distfile
        return distfile

    elif distname.endswith(".tar.gz"):
        distfile = TarGzDistribution(f)
        dists[distname] = distfile
        return distfile

    else:
        # Not supported
        return None

@pypi_bp.errorhandler(gunicorn.http.errors.ParseException)
def handle_bad_request(e):
    return abort(400)


@pypi_bp.route("/")
def index():
    if project := request.args.get("project"):
        return redirect(f"/project/{project}")
    return render_template("index.html")


@pypi_bp.route("/project/<project_name>/")
def versions(project_name):
    if project_name != canonicalize_name(project_name):
        return redirect(
            url_for("versions", project_name=canonicalize_name(project_name)), 301
        )

    resp = requests.get(f"https://pypi.org/pypi/{project_name}/json")
    pypi_project_url = f"https://pypi.org/project/{project_name}"

    if resp.status_code != 200:
        return redirect(pypi_project_url, 307)

    version_urls = [
        "." + "/" + str(version)
        for version in sorted(resp.json()["releases"].keys(), key=parse, reverse=True)
    ]
    return render_template(
        "links.html",
        links=version_urls,
        h2=project_name,
        h2_link=f"/project/{project_name}",
        h2_paren="View this project on PyPI",
        h2_paren_link=pypi_project_url,
    )


@pypi_bp.route("/project/<project_name>/<version>/")
def distributions(project_name, version):
    if project_name != canonicalize_name(project_name):
        return redirect(
            url_for(
                "distributions",
                project_name=canonicalize_name(project_name),
                version=version,
            ),
            301,
        )

    resp = requests.get(f"https://pypi.org/pypi/{project_name}/{version}/json")
    if resp.status_code != 200:
        return redirect(f"/project/{project_name}/")

    dist_urls = [
        "." + urllib.parse.urlparse(url["url"]).path + "/"
        for url in resp.json()["urls"]
    ]
    return render_template(
        "links.html",
        links=dist_urls,
        h2=f"{project_name}",
        h2_link=f"/project/{project_name}",
        h2_paren="View this project on PyPI",
        h2_paren_link=f"https://pypi.org/project/{project_name}",
        h3=f"{project_name}=={version}",
        h3_link=f"/project/{project_name}/{version}",
        h3_paren="View this release on PyPI",
        h3_paren_link=f"https://pypi.org/project/{project_name}/{version}",
    )


@pypi_bp.route(
    "/project/<project_name>/<version>/packages/<first>/<second>/<rest>/<distname>/"
)
def distribution(project_name, version, first, second, rest, distname):
    if project_name != canonicalize_name(project_name):
        return redirect(
            url_for(
                "distribution",
                project_name=canonicalize_name(project_name),
                version=version,
                first=first,
                second=second,
                rest=rest,
                distname=distname,
            ),
            301,
        )

    dist = _get_dist(first, second, rest, distname)

    if dist:
        file_urls = [
            "./" + urllib.parse.quote(filename) for filename in dist.namelist()
        ]
        return render_template(
            "links.html",
            links=file_urls,
            h2=f"{project_name}",
            h2_link=f"/project/{project_name}",
            h2_paren="View this project on PyPI",
            h2_paren_link=f"https://pypi.org/project/{project_name}",
            h3=f"{project_name}=={version}",
            h3_link=f"/project/{project_name}/{version}",
            h3_paren="View this release on PyPI",
            h3_paren_link=f"https://pypi.org/project/{project_name}/{version}",
            h4=distname,
            h4_link=f"/project/{project_name}/{version}/packages/{first}/{second}/{rest}/{distname}/",  # noqa
        )
    else:
        return "Distribution type not supported"


def mailto_report_link(project_name, version, file_path, request_url):
    """
    Generate a mailto report link for malicious code.
    """
    message_body = (
        "PyPI Malicious Package Report\n"
        "--\n"
        f"Package Name: {project_name}\n"
        f"Version: {version}\n"
        f"File Path: {file_path}\n"
        f"Inspector URL: {request_url}\n\n"
        "Additional Information:\n\n"
    )

    subject = f"Malicious Package Report: {project_name}"

    return (
        f"mailto:security@pypi.org?"
        f"subject={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(message_body)}"
    )


@pypi_bp.route(
    "/project/<project_name>/<version>/packages/<first>/<second>/<rest>/<distname>/<path:filepath>"  # noqa
)
def file(project_name, version, first, second, rest, distname, filepath):
    if project_name != canonicalize_name(project_name):
        return redirect(
            url_for(
                "file",
                project_name=canonicalize_name(project_name),
                version=version,
                first=first,
                second=second,
                rest=rest,
                distname=distname,
                filepath=filepath,
            ),
            301,
        )

    dist = _get_dist(first, second, rest, distname)
    if dist:
        try:
            contents = dist.contents(filepath)
        except UnicodeDecodeError:
            return "Binary files are not supported"
        except FileNotFoundError:
            return abort(404)

        report_link = mailto_report_link(project_name, version, filepath, request.url)
        return render_template(
            "code.html",
            code=contents,
            mailto_report_link=report_link,
            h2=f"{project_name}",
            h2_link=f"/project/{project_name}",
            h2_paren="View this project on PyPI",
            h2_paren_link=f"https://pypi.org/project/{project_name}",
            h3=f"{project_name}=={version}",
            h3_link=f"/project/{project_name}/{version}",
            h3_paren="View this release on PyPI",
            h3_paren_link=f"https://pypi.org/project/{project_name}/{version}",
            h4=distname,
            h4_link=f"/project/{project_name}/{version}/packages/{first}/{second}/{rest}/{distname}/",  # noqa
            h5=filepath,
            h5_link=f"/project/{project_name}/{version}/packages/{first}/{second}/{rest}/{distname}/{filepath}",  # noqa
        )
    else:
        return "Distribution type not supported"
