#!/usr/bin/env python3


import logging
import json
import time
import tomllib
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import warnings
import base64


import requests
import curl_cffi
from varboxes import VarBox
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from seleniumbase import SB


from pytolino import server_settings_keys
from pytolino import requests_keys
from pytolino import cache_folder


DOWNLOADED_EPUB_FN = "downloaded_epub.epub"
COVER_FN = "cover.png"
DELIVERABLE_ID = "deliverableId"
PUBLICATION_ID = "publicationId"
EPUB_METADATA = "epubMetaData"


class PytolinoException(Exception):
    pass


class ExpirationError(PytolinoException):
    pass


SERVERS_SETTINGS_FN = "servers_settings.toml"
SERVERS_SETTINGS_FP = Path(__file__).parent / SERVERS_SETTINGS_FN
servers_settings = tomllib.loads(SERVERS_SETTINGS_FP.read_text())
PARTNERS = servers_settings.keys()

COMMON_SETTINGS_FN = "common_settings.toml"
COMMON_SETTINGS_FP = Path(__file__).parent / COMMON_SETTINGS_FN
common_settings = tomllib.loads(COMMON_SETTINGS_FP.read_text())
client_id = common_settings["client_id"]
scope = common_settings["scope"]
redirect_uri = common_settings["redirect_uri"]
additional_request_parameters = common_settings[
    "additional_request_parameters"
]
devices_url = common_settings["devices_url"]
devices_list_headers = common_settings["headers"]["devices_list"]
token_headers = common_settings["headers"]["token"]
client_type = common_settings["client_type"]


def main():
    pass


class Client(object):
    """create a client to communicate with a tolino partner (login, etc..)"""

    _IMPERSONATE = "chrome"

    def _log_request(self, rsp: requests.Response, data=None):
        if rsp.ok:
            log = logging.debug
        else:
            log = logging.error
        log("=====request=======")
        log(rsp.url)
        log(rsp.request.method)
        log("data:")
        log(data)
        log("response:")
        log(rsp)
        log("response text:")
        log(rsp.text)
        log("request header:")
        log(rsp.request.headers)
        log("response header:")
        log(rsp.headers)
        log("===================")

        if not rsp.ok:
            raise PytolinoException("host response not ok")

    def _store_current_token(self):
        """store the token with attribute of self"""
        username = self._username
        vb = VarBox(app_name=f"{self._server_name}.{username}")
        vb.refresh_token = self._refresh_token
        vb.access_token = self._access_token
        vb.hardware_id = self._hardware_id
        vb.access_expiration_time = self._access_expiration_time
        vb.refresh_expiration_time = self._refresh_expiration_time

    def _retrieve_last_token(self):
        """retrieve token that was stored with this username"""
        username = self._username
        vb = VarBox(app_name=f"{self._server_name}.{username}")
        if not hasattr(vb, "refresh_token"):
            raise PytolinoException("there was no token stored for that name")
        self._refresh_token = vb.refresh_token
        self._access_token = vb.access_token
        self._hardware_id = vb.hardware_id
        self._access_expiration_time = vb.access_expiration_time
        self._refresh_expiration_time = vb.refresh_expiration_time

    def raise_for_access_expiration(self) -> bool:
        """verify if access token is expired"""
        if self._access_expiration_time < time.time():
            raise ExpirationError("access token is expired")

    def raise_for_refresh_expiration(self) -> bool:
        """verify if refresh token is expired"""
        now = time.time()
        if self._refresh_expiration_time < now:
            raise ExpirationError("refresh token is expired")

    @property
    def refresh_token(self) -> str:
        """refresh token to get new access token"""
        return self._refresh_token

    @property
    def hardware_id(self) -> str:
        """hardware id that is sent in request payloads"""
        return self._hardware_id

    @property
    def expires_in(self) -> int:
        """expiration time in second of access token"""
        return self._expires_in

    @property
    def refresh_expires_in(self) -> int:
        """expiration time (s) of refresh token"""
        return self._refresh_expires_in

    @property
    def access_expiration_time(self) -> float:
        """time (seconds from epoch) for expiration of access token"""
        return self._access_expiration_time

    @property
    def access_token(self) -> str:
        """value of access token"""
        return self._access_token

    def __init__(
        self,
        username: str,
        server_name="orellfuessli",
    ):

        if server_name not in servers_settings:
            raise PytolinoException(
                f"the partner {server_name} was not found."
                f"please choose one of the list: {PARTNERS}"
            )

        self._username = username
        self._server_name = server_name
        self._access_token = None
        self._refresh_token = None
        self._expires_in = None
        self._refresh_expires_in = None
        self._hardware_id = None
        self._access_expiration_time = 0
        self._refresh_expiration_time = 0
        self._user_agent = None

        self._server_settings = servers_settings[server_name]
        self._shadow_host_id = self._server_settings[
            server_settings_keys.SHADOW_HOST_ID
        ]
        self._username_field_id = self._server_settings[
            server_settings_keys.USERNAME_FIELD_ID
        ]
        self._username_field_id = self._server_settings[
            server_settings_keys.USERNAME_FIELD_ID
        ]
        self._cookie_deny_css = self._server_settings[
            server_settings_keys.COOKIE_DENY_CSS
        ]
        self._username_field_id = self._server_settings[
            server_settings_keys.USERNAME_FIELD_ID
        ]
        self._password_field_id = self._server_settings[
            server_settings_keys.PASSWORD_FIELD_ID
        ]
        self._submit_css = self._server_settings[
            server_settings_keys.SUBMIT_CSS
        ]
        self._login_url = self._server_settings[server_settings_keys.LOGIN_URL]
        self._auth_url = self._server_settings[server_settings_keys.AUTH_URL]
        self._token_url = self._server_settings[server_settings_keys.TOKEN_URL]
        self._partner_id = self._server_settings[
            server_settings_keys.PARTNER_ID
        ]
        self._upload_url = self._server_settings[
            server_settings_keys.UPLOAD_URL
        ]
        self._delete_url = self._server_settings[
            server_settings_keys.DELETE_URL
        ]
        self._cover_url = self._server_settings[server_settings_keys.COVER_URL]
        self._meta_url = self._server_settings[server_settings_keys.META_URL]
        self._sync_data_url = self._server_settings[
            server_settings_keys.SYNC_DATA_URL
        ]
        self._inventory_url = self._server_settings[
            server_settings_keys.INVENTORY_URL
        ]
        self._download_info_url = self._server_settings[
            server_settings_keys.DOWNLOAD_INFO_URL
        ]

        self._session = requests.Session()
        self._session_cffi = curl_cffi.Session()
        self._server_name = server_name

        try:
            self._retrieve_last_token()
        except PytolinoException as e:
            print(e)

    def import_token(self, refresh_token: str, hardware_id: str):
        """add manually a refresh token to GUI login

        :refresh_token: obtained from tolino(?) or during a manual
        login and inspector tool
        :hardware_id:

        """
        self._refresh_token = refresh_token
        self._hardware_id = hardware_id
        try:
            self._renew_access_token()
        except PytolinoException as e:
            logging.error(e)
            logging.error(
                "could not get a new access token with this refresh token"
            )

    def _get_auth_headers(self):
        headers = {
            requests_keys.T_AUTH_TOKEN: self.access_token,
            requests_keys.HARDWARE_ID: self.hardware_id,
            requests_keys.RESELLER_ID: self._partner_id,
        }
        return headers

    def _renew_access_token(self):
        """get a new access and refresh tokens."""

        headers = token_headers
        data = dict(
            client_id=client_id,
            grant_type=requests_keys.REFRESH_TOKEN,
            refresh_token=self.refresh_token,
            scope=scope,
        )
        url = self._token_url
        host_response = self._session_cffi.post(
            url,
            data=data,
            verify=True,
            allow_redirects=True,
            headers=headers,
            impersonate=self._IMPERSONATE,
        )
        self._log_request(host_response, data)

        self._read_and_store_token_response(host_response)
        self._store_current_token()
        logging.info("got a new access token!")
        logging.info(f"access will expire in {self._expires_in}s")
        logging.info(f"refresh will expire in {self._refresh_expires_in}s")

    def _get_login_cookies(self, password):

        timeout = 10

        try:
            with SB(uc=True) as sb:
                driver = sb.driver
                driver.implicitly_wait(timeout)
                url = self._login_url
                driver.get(url)

                # deny cookies
                shadow_host_id = self._shadow_host_id
                shadow_host = driver.find_element(By.ID, shadow_host_id)
                shadow_root = shadow_host.shadow_root
                css = self._cookie_deny_css
                wait = WebDriverWait(shadow_root, timeout)
                deny_button = wait.until(
                    expected_conditions.element_to_be_clickable(
                        (By.CSS_SELECTOR, css)
                    )
                )
                deny_button.click()

                # fill credentials and submit
                username_field_id = self._username_field_id
                username_field = driver.find_element(
                    By.ID,
                    username_field_id,
                )
                password_field_id = self._password_field_id
                password_field = driver.find_element(
                    By.ID,
                    password_field_id,
                )
                css = self._submit_css
                submit_button = driver.find_element(
                    By.CSS_SELECTOR,
                    css,
                )
                username_field.send_keys(self._username)
                password_field.send_keys(password)
                wait = WebDriverWait(driver, timeout=timeout)
                wait.until(
                    expected_conditions.element_to_be_clickable(submit_button)
                )
                submit_button.click()

                # get cookies
                cookies = driver.get_cookies()
                user_agent = driver.get_user_agent()
                self._user_agent = user_agent
        except TimeoutException:
            raise PytolinoException("timeout error during login")
        else:
            for cookie in cookies:
                self._session_cffi.cookies.set(cookie["name"], cookie["value"])
                self._session.cookies.set(cookie["name"], cookie["value"])

    def _get_auth_code(self):

        url = self._auth_url
        LOCATION = "location"
        CODE = "code"

        params = dict(
            client_id=client_id,
            response_type=CODE,
            scope=scope,
            redirect_uri=redirect_uri,
        )
        params.update(additional_request_parameters)

        host_response = self._session_cffi.get(
            url,
            params=params,
            verify=True,
            allow_redirects=False,
            impersonate=self._IMPERSONATE,
        )
        self._log_request(host_response, params)
        headers = host_response.headers
        try:
            location_url = headers[LOCATION]
        except KeyError:
            raise PytolinoException(
                "failed to get auth code, response headers has no location key"
            )
        else:
            query_str = urlparse(location_url).query
            location_parameters = parse_qs(query_str)
            auth_code = location_parameters[CODE][0]
        return auth_code

    def _add_user_agent(self, headers: dict) -> dict:
        if self._user_agent:
            user_agent = self._user_agent
            headers[requests_keys.USERAGENT] = user_agent
        return headers

    def _get_token(self, auth_code: str):

        data = dict(
            client_id=client_id,
            grant_type=requests_keys.AUTHORIZATION_CODE,
            code=auth_code,
            scope=scope,
            redirect_uri=redirect_uri,
        )
        data.update(additional_request_parameters)

        headers = token_headers
        url = self._token_url
        host_response = self._session_cffi.post(
            url,
            data=data,
            verify=True,
            allow_redirects=False,
            headers=headers,
            impersonate=self._IMPERSONATE,
        )
        self._log_request(host_response, data)
        self._read_and_store_token_response(host_response)

    def _read_and_store_token_response(self, host_response):
        try:
            data_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "could not read token response because of json error"
            )
        else:
            try:
                self._access_token = data_rsp[requests_keys.ACCESS_TOKEN]
                self._refresh_token = data_rsp[requests_keys.REFRESH_TOKEN]
                self._expires_in = data_rsp[requests_keys.EXPIRES_IN]
                self._refresh_expires_in = data_rsp[
                    requests_keys.REFRESH_EXPIRES_IN
                ]
            except KeyError:
                raise PytolinoException(
                    "could not read token response because of key error"
                )
            else:
                now = time.time()
                self._access_expiration_time = now + self._expires_in
                self._refresh_expiration_time = now + self._refresh_expires_in

    def _get_hardware_id(self):
        url = devices_url
        account = {
            requests_keys.AUTH_TOKEN: self._access_token,
            requests_keys.RESELLER_ID: self._partner_id,
        }
        accounts = [account]
        data_dict = {
            requests_keys.DEVICE_LIST_REQUEST: {
                requests_keys.ACCOUNTS: accounts
            }
        }
        data = json.dumps(data_dict)
        headers = devices_list_headers
        headers[requests_keys.T_AUTH_TOKEN] = self._access_token
        headers[requests_keys.RESELLER_ID] = self._partner_id
        host_response = self._session.post(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        j = host_response.json()
        devices = j[requests_keys.DEVICE_LIST_RESPONSE][requests_keys.DEVICES]
        devices.sort(key=lambda el: el[requests_keys.DEVICE_LAST_USAGE])
        my_dev = devices[-1]
        hardware_id = my_dev[requests_keys.DEVICE_ID]
        self._hardware_id = hardware_id

    def login(self, password, allow_GUI_autologin=True):
        """login to the partner and get access token."""
        logged_in = False
        try:
            self.raise_for_access_expiration()
        except ExpirationError:
            try:
                self.raise_for_refresh_expiration()
            except ExpirationError:
                get_a_new_token = False
            else:
                get_a_new_token = True
        else:
            get_a_new_token = True

        if get_a_new_token:
            try:
                logging.info("ask for new access token...")
                self._renew_access_token()
            except PytolinoException as e:
                logging.warning(e)
                logging.warning("previous access token could not be renewed")
            else:
                logged_in = True

        if not logged_in and allow_GUI_autologin:
            self._get_login_cookies(password)
            auth_code = self._get_auth_code()
            self._get_token(auth_code)
            self._get_hardware_id()
            self._store_current_token()
            logged_in = True
        if not logged_in:
            raise PytolinoException("could not login")

    def logout(self):
        """logout from tolino partner host"""
        raise NotImplementedError("logout is not necessary with tokens")

    def register(self):
        raise NotImplementedError("register is not necessary with tokens")

    def unregister(self, device_id=None):
        raise NotImplementedError("unregister is not necessary with tokens")

    def get_inventory(self):
        """download a list of the books on the cloud and their information
        :returns: list of dict describing the book, with a epubMetaData dict

        """

        url = self._inventory_url
        headers = self._get_auth_headers()
        params = {"strip": "true"}
        host_response = self._session.get(
            url,
            params=params,
            headers=headers,
        )
        self._log_request(host_response, params)

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "inventory list request failed because of json error."
            )
        else:
            try:
                publication_inventory = j["PublicationInventory"]
                uploaded_ebooks = publication_inventory["edata"]
                purchased_ebook = publication_inventory["ebook"]
            except KeyError:
                raise PytolinoException(
                    "inventory list request failed because",
                    "of key error in json.",
                )
            else:
                inventory = uploaded_ebooks + purchased_ebook
                return inventory

    def mark_book_as_finished(self, book_id):
        """TODO: Docstring for mark_book_as_finished.

        :book_id: TODO
        :returns: TODO

        """
        payload = {
            "revision": None,
            "patches": [
                {
                    "op": "add",
                    "value": {
                        "modified": round(time.time() * 1000),
                        "name": "collection_finished_readings_name",
                        "category": "system",
                    },
                    "path": f"/publications/{book_id}/tags",
                }
            ],
        }
        data = json.dumps(payload)

        url = self._sync_data_url
        headers = self._get_auth_headers()
        headers[requests_keys.CONTENT_TYPE] = "application/json"
        headers[requests_keys.CLIENT_TYPE] = client_type
        host_response = self._session.patch(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        try:
            json_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "could not get info from request. answer not json"
            )
        else:
            revision = json_rsp["revision"]
            patches = json_rsp["patches"]
            patch = self._get_last_patch(patches)
            patch_rev = patch["value"]["revision"]
            return revision, patch_rev, patch

    def add_to_collection(self, book_id, collection_name):
        """add a book to a collection on the cloud

        :book_id: identify the book on the cloud
        :collection_name: str name

        """

        payload = {
            "revision": None,
            "patches": [
                {
                    "op": "add",
                    "value": {
                        "modified": round(time.time() * 1000),
                        "name": collection_name,
                        "category": "collection",
                    },
                    "path": f"/publications/{book_id}/tags",
                }
            ],
        }
        data = json.dumps(payload)

        url = self._sync_data_url
        headers = self._get_auth_headers()
        headers[requests_keys.CONTENT_TYPE] = "application/json"
        headers[requests_keys.CLIENT_TYPE] = client_type
        host_response = self._session.patch(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        try:
            json_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "could not get info from request. answer not json"
            )
        else:
            revision = json_rsp["revision"]
            patch = self._get_patch_from_last_added_collection_to_book(
                json_rsp,
                book_id,
            )
            patch_rev = patch["value"]["revision"]
            return revision, patch_rev, patch

    def _sync_request(self):
        payload = {"revision": None, "patches": []}
        data = json.dumps(payload)

        url = self._sync_data_url
        headers = self._get_auth_headers()
        headers[requests_keys.CONTENT_TYPE] = "application/json"
        headers[requests_keys.CLIENT_TYPE] = client_type
        host_response = self._session.patch(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        try:
            json_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException("sync request failed. answer not json")
        else:
            return json_rsp

    def get_sync_data(self):
        """request sync data to get all patches of tags, etc...
        :returns: revision, patches

        """
        json_rsp = self._sync_request()
        revision = json_rsp["revision"]
        if "patches" in json_rsp:
            patches = {
                patch["value"]["revision"]: patch
                for patch in json_rsp["patches"]
            }
        else:
            patches = dict()
        return revision, patches

    def get_book_id_from_patch(self, patch):
        """parse patch to get book id

        :patch: comes from sync_data
        :returns: book_id

        """
        path = patch["path"]
        ebook_id = path.split("/")[2]
        return ebook_id

    def _get_patch_from_last_added_collection_to_book(self, data, ebook_id):
        patches = data["patches"]
        book_patches = [
            patch for patch in patches if ebook_id in patch["path"]
        ]
        if not book_patches:
            return None
        book_collection_patches = [
            patch
            for patch in patches
            if patch["value"].get("category") == "collection"
        ]
        if not book_collection_patches:
            return None
        book_collection_patches.sort(key=lambda el: el["value"]["modified"])
        last_patch = book_collection_patches[-1]
        return last_patch

    def _get_last_patch(self, patches):
        patches.sort(key=lambda el: el["value"]["modified"])
        last_patch = patches[-1]
        return last_patch

    def _get_patch_for_book_add_to_collection(
        self, patches, ebook_id, collection_name
    ):
        book_patches = [
            patch for patch in patches if ebook_id in patch["path"]
        ]
        if not book_patches:
            return None
        book_collection_patches = [
            patch
            for patch in book_patches
            if patch["value"].get("category") == "collection"
        ]
        if not book_collection_patches:
            return None
        collection_name_patches = [
            patch
            for patch in book_collection_patches
            if patch["value"]["name"] == collection_name
        ]
        if not collection_name_patches:
            return None
        else:
            return collection_name_patches.pop()

    def _get_patch_book_marked_as_finished(self, patches, ebook_id):
        book_patches = [
            patch for patch in patches if ebook_id in patch["path"]
        ]
        if not book_patches:
            return None
        book_system_patches = [
            patch
            for patch in book_patches
            if patch["value"].get("category") == "system"
        ]
        if not book_system_patches:
            return None
        finish_patches = [
            patch
            for patch in book_system_patches
            if patch["value"]["name"] == "collection_finished_readings_name"
        ]
        if not finish_patches:
            return None
        else:
            return finish_patches.pop()

    def mark_book_as_not_finished(self, book_id):
        """remove the finished label on the book

        :book_id: TODO
        :returns: TODO

        """
        data = self._sync_request()
        patches = data["patches"]
        patch = self._get_patch_book_marked_as_finished(patches, book_id)
        if patch is None:
            msg = (
                "could not get last patch from server."
                "book is either not present or was not marked as finished"
            )
            raise PytolinoException(msg)

        revision_value = patch["value"]["revision"]
        revision = data["revision"]
        path = patch["path"]

        payload = {
            "revision": revision,
            "patches": [
                {
                    "op": "remove",
                    "value": {
                        "modified": round(time.time() * 1000),
                        "name": "collection_finished_readings_name",
                        "category": "system",
                        "revision": revision_value,
                    },
                    "path": path,
                }
            ],
        }
        data = json.dumps(payload)

        url = self._sync_data_url
        headers = self._get_auth_headers()
        headers[requests_keys.CONTENT_TYPE] = "application/json"
        headers[requests_keys.CLIENT_TYPE] = client_type
        host_response = self._session.patch(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        try:
            json_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "could not get info from request. answer not json"
            )
        else:
            revision = json_rsp["revision"]
            patch = json_rsp["patches"].pop()
            patch_rev = patch["value"]["revision"]
            return revision, patch_rev, patch

    def rm_book_from_collection(self, book_id, collection_name):
        """remove a book from a collection (book is not deleted)

        :book_id: identify the book on the cloud
        :collection_name: str name

        """
        data = self._sync_request()
        patches = data["patches"]
        patch = self._get_patch_for_book_add_to_collection(
            patches, book_id, collection_name
        )
        if patch is None:
            msg = (
                "could not get last patch from server."
                "the book is probably not part from this collection"
                "any more"
            )
            raise PytolinoException(msg)

        revision_value = patch["value"]["revision"]
        revision = data["revision"]
        path = patch["path"]

        payload = {
            "revision": revision,
            "patches": [
                {
                    "op": "remove",
                    "value": {
                        "modified": round(time.time() * 1000),
                        "name": collection_name,
                        "category": "collection",
                        "revision": revision_value,
                    },
                    "path": path,
                }
            ],
        }
        data = json.dumps(payload)

        url = self._sync_data_url
        headers = self._get_auth_headers()
        headers[requests_keys.CONTENT_TYPE] = "application/json"
        headers[requests_keys.CLIENT_TYPE] = client_type
        host_response = self._session.patch(
            url,
            data=data,
            headers=headers,
        )
        self._log_request(host_response, data)
        try:
            json_rsp = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException(
                "could not get info from request. answer not json"
            )
        else:
            revision = json_rsp["revision"]
            patch = json_rsp["patches"].pop()
            patch_rev = patch["value"]["revision"]
            return revision, patch_rev, patch

    def upload_metadata(self, book_id, **new_metadata):
        """upload some metadata to a specific book on the cloud

        :book_id: ref on the cloud of the book
        :**meta_data: dict of metadata than can be changed

        """

        url = self._meta_url
        params = {requests_keys.DELIVERABLE_ID: book_id}
        headers = self._get_auth_headers()
        host_response = self._session.get(
            url,
            params=params,
            headers=headers,
        )
        self._log_request(host_response, params)

        try:
            book = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException("metadata upload failed. answer not json")
        else:
            for key, value in new_metadata.items():
                book["metadata"][key] = value
            payload = {requests_keys.UPLOAD_METADATA: book["metadata"]}
            data = json.dumps(payload)
            headers = self._get_auth_headers()
            headers[requests_keys.CONTENT_TYPE] = "application/json"

            host_response = self._session.put(
                url,
                data=data,
                headers=headers,
            )
        self._log_request(host_response, data)

    def _download_info(self, publication_id: str, deliverable_id):
        xxx = base64.b64encode(bytes(publication_id, "utf-8")).decode("utf-8")
        yyy = base64.b64encode(bytes(deliverable_id, "utf-8")).decode("utf-8")
        url = self._download_info_url.format(xxx, yyy)
        headers = self._get_auth_headers()
        host_response = self._session.get(
            url,
            headers=headers,
        )
        self._log_request(host_response)

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException("download info failed. answer not json")
        else:
            try:
                download_info = j["DownloadInfo"]
                content_url = download_info["contentUrl"]
                return content_url
            except KeyError:
                raise PytolinoException(
                    "download info failed.no info found in response"
                )

    def _get_book_data(self, identifier):
        inventory = self.get_inventory()
        matched_books = [
            book for book in inventory if book[PUBLICATION_ID] == epub_id
        ]
        matched_books = [
            book for book in inventory if book[EPUB_METADATA]["identifier"] == identifier
        ]
        if not matched_books:
            raise PytolinoException("no book on the cloud with this id")
        return matched_books[0]

    def download(self, identifier: str) -> tuple[Path, Path, dict]:
        """download book from cloud

        :epub_id:
        :returns: ebook path, cover path, metadata

        """
        book_data = self._get_book_data(identifier)
        deliverable_id = book_data[DELIVERABLE_ID]
        publication_id = book_data[PUBLICATION_ID]
        url = self._download_info(publication_id, deliverable_id)

        headers = self._get_auth_headers()
        host_response = self._session.get(
            url,
            headers=headers,
        )
        epub_fp = cache_folder / DOWNLOADED_EPUB_FN
        self._log_request(host_response)
        with open(epub_fp, "wb") as file:
            file.write(host_response.content)
        all_metadata = book_data[EPUB_METADATA]
        author_list = all_metadata["author"]
        authors = ",".join([author["name"] for author in author_list])
        metadata = dict(
            title=all_metadata.get("title"),
            isbn=all_metadata.get("isbn"),
            languages=all_metadata.get("language"),
            authors=authors,
            publisher=all_metadata.get("publisher"),
            issued=all_metadata["issued"],
        )
        file_resource = all_metadata["fileResource"]
        if file_resource:
            cover_url = file_resource[0]["resource"]
            cover_path = self._download_cover(cover_url)
        else:
            cover_path = None
        return epub_fp, cover_path, metadata

    def _download_cover(self, cover_url):
        headers = self._get_auth_headers()
        url = cover_url
        host_response = self._session.get(
            url,
            headers=headers,
        )
        self._log_request(host_response)
        cover_fp = cache_folder / COVER_FN
        with open(cover_fp, "wb") as file:
            file.write(host_response.content)
        return cover_fp

    def upload(
        self,
        file_path: Path or str,
        name=None,
    ):
        """upload an ebook to your cloud

        :file_path: str path to the ebook to upload
        :name: str name of book if different from filename
        :extension: epub or pdf, if not in filename
        :returns: epub_id on the server

        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            warnings.warn(
                "file_path arg should better be a Path object",
                DeprecationWarning,
            )

        if name is None:
            name = file_path.name
        extension = file_path.suffix

        epubmime = "application/epub+zip"
        pdfmime = "application/pdf"
        mime = epubmime if extension == ".epub" else pdfmime

        url = self._upload_url
        headers = self._get_auth_headers()
        with open(file_path, "rb") as ebook_file:
            files = [("file", (name, ebook_file, mime))]
            host_response = self._session.post(
                url,
                files=files,
                headers=headers,
            )
        self._log_request(host_response, files)

        try:
            j = host_response.json()
        except requests.JSONDecodeError:
            raise PytolinoException("file upload failed. answer not json")
        else:
            try:
                return j["metadata"]["deliverableId"]
            except KeyError:
                raise PytolinoException(
                    "file upload failed.no metadata or deliverableId in response"
                )

    def delete_ebook(self, ebook_id):
        """delete an ebook present on your cloud

        :ebook_id: id of the ebook to delete.
        :returns: None

        """
        url = self._delete_url
        params = {requests_keys.DELIVERABLE_ID: ebook_id}
        headers = self._get_auth_headers()
        host_response = self._session.get(
            url,
            params=params,
            headers=headers,
        )
        self._log_request(host_response, params)

    def add_cover(self, book_id, filepath: Path or str):
        """upload a a cover to a book on the cloud

        :book_id: id of the book on the serveer
        :filepath: path to the cover file
        :file_ext: png, jpg or jpeg. only necessary if the
        filepath has no extension

        """
        FILENAME = "1092560016"  # example from tolino api doc. different?

        if isinstance(filepath, str):
            filepath = Path(filepath)
            warnings.warn(
                "file_path arg should better be a Path object",
                DeprecationWarning,
            )

        ext = filepath.suffix

        mime = {
            ".png": "image/png",
            ".jpeg": "image/jpeg",
            ".jpg": "image/jpeg",
        }.get(ext.lower(), "application/jpeg")

        url = self._cover_url
        data = {requests_keys.DELIVERABLE_ID: book_id}
        headers = self._get_auth_headers()
        with open(filepath, "rb") as cover_file:
            files = [("file", (FILENAME, cover_file, mime))]
            host_response = self._session.post(
                url,
                files=files,
                data=data,
                headers=headers,
            )
        self._log_request(host_response, data)


if __name__ == "__main__":
    main()
