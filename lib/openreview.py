"""
openreview.py
20230104
"""

import time
from requests import options
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import SessionNotCreatedException
import os
import shutil
# https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename
from slugify import slugify
from lib.downloader import Downloader, shorten_title, \
    is_valid_downloaded_file
from lib.proxy import get_proxy
from lib import graceful_exit
import urllib
import base64
import atexit
import random
import re
from lib.arxiv import get_pdf_link_from_arxiv

try:
    import undetected_chromedriver as uc
    _HAS_UNDETECTED_CHROMEDRIVER = True
except ImportError:
    _HAS_UNDETECTED_CHROMEDRIVER = False

# browsers opened by this module, quit at exit even when the script is
# interrupted by Ctrl+C (SystemExit skips the normal driver.quit() calls,
# leaving zombie chrome processes that lock the user profile directory)
_opened_drivers = []


def _register_driver_for_cleanup(driver):
    _opened_drivers.append(driver)


def _cleanup_opened_drivers():
    for driver in _opened_drivers:
        try:
            driver.quit()
        except Exception:
            pass


atexit.register(_cleanup_opened_drivers)


def _get_chrome_full_version():
    """
    the full version of the installed Chrome, e.g. "151.0.7922.76" (the
    version folder in the Chrome install directory). The chromedriver
    download needs the exact full version.
    :return: str or None
    """
    import glob
    candidates = [
        os.environ.get('PROGRAMFILES', 'C:/Program Files'),
        os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome'),
    ]
    for base in candidates:
        pattern = os.path.join(base, 'Google', 'Chrome', 'Application',
                               '[0-9]*')
        dirs = sorted(glob.glob(pattern))
        if dirs:
            return os.path.basename(dirs[-1])
    return None


def _get_chrome_major_version():
    """
    get the major version of the installed Chrome, used to select a matching
    chromedriver for undetected_chromedriver, e.g. if the latest chromedriver
    targets Chrome version N+1 while the installed Chrome is still version N.
    :return: int or None
    """
    full_version = _get_chrome_full_version()
    if full_version is None:
        return None
    return int(full_version.split('.')[0])


def _mirror_chromedriver_dir():
    """
    the cache directory of the chromedriver downloaded from the mirror,
    keyed by the full Chrome version so that a Chrome update downloads the
    matching driver automatically
    :return: str or None
    """
    full_version = _get_chrome_full_version()
    if full_version is None:
        return None
    return os.path.join(os.path.expanduser('~'), '.cache',
                        'chromedriver_mirror', full_version)


def _cached_mirror_chromedriver():
    """
    the path of the chromedriver previously downloaded from the mirror for
    the installed Chrome, or None if not cached. undetected_chromedriver
    patches the driver in place and reuses it, so a cached driver avoids
    any network access on the next launch.
    :return: str or None
    """
    cache_dir = _mirror_chromedriver_dir()
    if cache_dir is None:
        return None
    exe_path = os.path.join(cache_dir, 'chromedriver.exe')
    if os.path.exists(exe_path):
        return exe_path
    return None


def _latest_mirror_build_for(major):
    """
    the newest chromedriver build of the given Chrome major version that
    the npmmirror mirror currently has, or None. The mirror lags behind the
    Google releases, so the exact installed build may be missing; any build
    of the same major version works with the installed Chrome (this matches
    how undetected_chromedriver itself selects a driver via the
    LATEST_RELEASE_<major> file).
    :param major: int, the Chrome major version
    :return: str or None, e.g. "151.0.7922.138"
    """
    import requests
    try:
        resp = requests.get(
            'https://registry.npmmirror.com/-/binary/chrome-for-testing/',
            timeout=30, verify=False)
        if resp.status_code != 200:
            return None
        names = [e.get('name', '').rstrip('/') for e in resp.json()
                 if isinstance(e, dict) and e.get('name')]
        same_major = sorted(
            (n for n in names if n.startswith(f'{major}.')),
            key=lambda v: tuple(int(x) for x in v.split('.')),
            reverse=True)
        return same_major[0] if same_major else None
    except Exception as e:
        print(f'failed to list the mirror chromedriver versions: {e}')
        return None


def _download_chromedriver_from_mirror():
    """
    download a chromedriver matching the installed Chrome from the npmmirror
    binary mirror, as a fallback when undetected_chromedriver cannot fetch
    its own driver from the Google endpoints (they are blocked from this
    network, or the TLS-interception CA is not in Python's trust store). The
    file is the official Google chromedriver binary hosted on the mirror;
    TLS verification is skipped because the interception CA is unknown to
    Python while the browser itself works normally.
    :return: str, the path of the downloaded chromedriver.exe, or None
    """
    import zipfile
    import urllib3
    import requests
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    full_version = _get_chrome_full_version()
    if full_version is None:
        print('cannot find the installed Chrome version, abort the '
              'chromedriver mirror download')
        return None
    cache_dir = os.path.join(os.path.expanduser('~'), '.cache',
                             'chromedriver_mirror', full_version)
    exe_path = os.path.join(cache_dir, 'chromedriver.exe')
    if os.path.exists(exe_path):
        return exe_path
    major = int(full_version.split('.')[0])
    build = _latest_mirror_build_for(major)
    if build is None:
        print(f'no chromedriver of Chrome {major} found on the npmmirror '
              f'mirror, abort the mirror download')
        return None
    if build != full_version:
        print(f'the mirror does not have chromedriver {full_version} yet, '
              f'using {build} (same Chrome major, safe)')
    base_url = 'https://registry.npmmirror.com/-/binary/chrome-for-testing/'
    zip_url = f'{base_url}{build}/win64/chromedriver-win64.zip'
    print(f'downloading chromedriver {build} from {zip_url} ...')
    try:
        # the mirror is trusted; verification is disabled because the
        # network's TLS-interception CA is not in Python's trust store
        resp = requests.get(zip_url, stream=True, timeout=60, verify=False)
        if resp.status_code != 200:
            print(f'chromedriver mirror download failed, HTTP '
                  f'{resp.status_code}')
            return None
        os.makedirs(cache_dir, exist_ok=True)
        zip_path = os.path.join(cache_dir, 'chromedriver-win64.zip')
        with open(zip_path, 'wb') as f:
            for chunk in resp.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(cache_dir)
        os.remove(zip_path)
        extracted_dir = os.path.join(cache_dir, 'chromedriver-win64')
        extracted = os.path.join(extracted_dir, 'chromedriver.exe')
        if os.path.exists(extracted):
            os.replace(extracted, exe_path)
            # the zip also contains LICENSE/NOTICE files in the same dir
            shutil.rmtree(extracted_dir, ignore_errors=True)
        if not os.path.exists(exe_path):
            print('chromedriver.exe not found inside the downloaded zip, '
                  'abort the mirror download')
            return None
        print(f'chromedriver downloaded to {exe_path}')
        return exe_path
    except Exception as e:
        print(f'chromedriver mirror download failed: {e}')
        return None


def _kill_stale_browsers(profile_dir):
    """
    the second Ctrl+C (force exit, os._exit) skips the atexit cleanup,
    leaving zombie chrome processes that lock the profile directory and
    make the next launch fail with "cannot connect to chrome". Kill any
    leftover chrome/chromedriver process that uses this profile dir.
    :param profile_dir: str, the Chrome user data directory
    :return: None
    """
    import subprocess
    ps_script = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -match 'chrome|chromedriver' -and "
        f"$_.CommandLine -like '*{profile_dir}*' }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force "
        "-ErrorAction SilentlyContinue }"
    )
    subprocess.run(['powershell', '-NoProfile', '-Command', ps_script],
                   capture_output=True, timeout=60)


def _repair_broken_profile(profile_dir):
    """
    Chrome 151 crashes at startup with a std::length_error when the
    "Account Web Data" SQLite database in the profile is corrupted (it gets
    corrupted when the browser is hard-killed during a database write,
    e.g. by the force-exit Ctrl+C or a taskkill). Delete the corrupt
    database files so that Chrome recreates them on the next launch.
    :param profile_dir: str, the Chrome user data directory
    :return: None
    """
    default_dir = os.path.join(profile_dir, 'Default')
    if not os.path.isdir(default_dir):
        return
    for name in os.listdir(default_dir):
        if name.startswith('Account Web Data') or \
                name.startswith('History') or \
                name.startswith('Web Data') or \
                name == 'Top Sites':
            path = os.path.join(default_dir, name)
            try:
                os.remove(path)
                print(f'repaired broken profile: removed {path}')
            except Exception:
                pass


def _force_gc(driver):
    """
    a long run navigates hundreds of pages in one tab, so the renderer's
    DOM / JS heap keeps growing page after page and eventually the browser
    runs out of memory. Force a V8 garbage collection on each page to
    release the previous page's memory.
    :param driver: selenium webdriver
    :return: None
    """
    try:
        driver.execute_cdp_cmd('HeapProfiler.collectGarbage', {})
    except Exception:
        pass


def get_driver(proxy_ip_port=None):
    # use a persistent Chrome profile, so that the passed Cloudflare check
    # and/or the OpenReview login session survive between runs
    profile_dir = os.path.join(
        os.path.expanduser('~'), '.openreview_chrome_profile')
    _kill_stale_browsers(profile_dir)

    if _HAS_UNDETECTED_CHROMEDRIVER:
        # undetected-chromedriver patches chromedriver (removes the cdc_
        # markers) and applies stealth settings, so that the Cloudflare
        # Turnstile check inside the OpenReview page can be passed manually
        # in the browser window, without logging in
        print('using undetected_chromedriver...')
        version_main = _get_chrome_major_version()
        if version_main is not None:
            print(f'Chrome major version: {version_main}')
        def _make_uc_options():
            # a fresh ChromeOptions object per uc.Chrome() call: the driver
            # mutates the options object, so reusing it on a retry raises
            # "you cannot reuse the ChromeOptions object"
            options = uc.ChromeOptions()
            if proxy_ip_port is not None:
                options.add_argument(f'--proxy-server={proxy_ip_port}')
            return options

        def _launch_uc(driver_path):
            """
            launch uc.Chrome with the profile-repair retry loop; raises the
            exception if the profile stays broken
            :param driver_path: str or None, the chromedriver path passed to
                undetected_chromedriver (None lets uc fetch its own driver)
            :return: selenium webdriver
            """
            try:
                return uc.Chrome(options=_make_uc_options(),
                                 user_data_dir=profile_dir,
                                 version_main=version_main,
                                 driver_executable_path=driver_path)
            except SessionNotCreatedException:
                # the profile may be broken: a corrupted "Account Web Data"
                # sqlite database makes Chrome crash at startup. Repair the
                # profile and retry once.
                print('Chrome failed to launch, repairing the profile and '
                      'retrying...')
                _repair_broken_profile(profile_dir)
                try:
                    return uc.Chrome(options=_make_uc_options(),
                                     user_data_dir=profile_dir,
                                     version_main=version_main,
                                     driver_executable_path=driver_path)
                except SessionNotCreatedException:
                    # the repair is not enough (e.g. other profile files are
                    # corrupted too): move the whole profile aside and start
                    # with a fresh one. The Cloudflare check / OpenReview
                    # login then has to be passed again.
                    _kill_stale_browsers(profile_dir)
                    backup = profile_dir + '.broken-' + \
                        time.strftime('%Y%m%d-%H%M%S')
                    try:
                        os.rename(profile_dir, backup)
                        print(f'profile still broken, moved it to {backup} '
                              f'and starting with a fresh profile (the '
                              f'Cloudflare check / login must be passed '
                              f'again)...')
                    except OSError:
                        # a leftover chrome process may lock a file; kill
                        # the browsers and remove the broken profile dir
                        shutil.rmtree(profile_dir, ignore_errors=True)
                        print('profile still broken, removed it and starting '
                              'with a fresh profile (the Cloudflare check / '
                              'login must be passed again)...')
                    return uc.Chrome(options=_make_uc_options(),
                                     user_data_dir=profile_dir,
                                     version_main=version_main,
                                     driver_executable_path=driver_path)

        try:
            # use the previously mirrored chromedriver when available, so
            # that uc never has to reach the (blocked) Google endpoints
            driver = _launch_uc(_cached_mirror_chromedriver())
        except OSError as e:
            # uc's patcher always re-downloads its own chromedriver from the
            # Google endpoints, which are unreachable from this network (the
            # TLS-interception CA is not in Python's trust store, raising
            # ssl.SSLCertVerificationError / urllib.error.URLError, both
            # OSErrors). Fall back to the official chromedriver downloaded
            # from the npmmirror mirror; uc patches it in place afterwards.
            if _cached_mirror_chromedriver() is not None:
                raise  # the cached mirror driver itself failed, do not retry
            print(f'failed to fetch the chromedriver from the Google '
                  f'endpoints ({e}), downloading it from the npmmirror '
                  f'mirror instead...')
            driver_path = _download_chromedriver_from_mirror()
            if driver_path is None:
                raise
            driver = _launch_uc(driver_path)
        # large pdfs may take a long time to download through the browser's
        # fetch, give the async script a generous timeout
        driver.set_script_timeout(600)
        _register_driver_for_cleanup(driver)
        return driver

    # fallback: plain selenium webdriver
    # driver = webdriver.Chrome(driver_path)
    capabilities = webdriver.DesiredCapabilities.CHROME
    if proxy_ip_port is not None:
        proxy = get_proxy(proxy_ip_port)
        proxy.add_to_capabilities(capabilities)

    # https://stackoverflow.com/a/78797164
    print('Installing chromedriver...')
    chrome_install = ChromeDriverManager().install()
    folder = os.path.dirname(chrome_install)
    chromedriver_path = os.path.join(folder, "chromedriver.exe")

    # https://stackoverflow.com/a/53040904
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={profile_dir}")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(
        options=options,
        service=Service(executable_path=chromedriver_path),
        desired_capabilities=capabilities)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    # NOTE: do NOT override navigator.userAgent. If the overridden version
    # differs from the real Chrome version reported by the Client Hints
    # (navigator.userAgentData), Cloudflare flags the browser as a bot.
    # large pdfs may take a long time to download through the browser's
    # fetch, give the async script a generous timeout
    driver.set_script_timeout(600)
    _register_driver_for_cleanup(driver)
    return driver


def wait_until_pass_challenge(driver, timeout_in_seconds=900):
    """
    If the current page is OpenReview's Cloudflare challenge page (Turnstile),
    print instructions and wait for the user to pass the check manually,
    e.g., sign in to OpenReview (which skips the check), until the original
    page (with the #notes element) loads.
    :param driver: selenium webdriver
    :param timeout_in_seconds: int, max waiting time in seconds. Default: 900.
    :return: None
    """
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[contains(@class, "cf-turnstile")]')))
    except Exception:
        return  # no challenge, the page loads normally
    print('*' * 70)
    print('OpenReview has been intercepted by a Cloudflare human check!')
    print('Please pass the check in the browser window (no login needed):')
    print('  1. Click the captcha checkbox and wait for it to verify; or')
    print('  2. Click the "Sign in" link and log in to your OpenReview')
    print('     account, which also skips the check.')
    print(f'Waiting at most {timeout_in_seconds} seconds for you...')
    print('*' * 70)
    # poll in small slices so that the first Ctrl+C can interrupt this
    # long wait as soon as possible
    wait = WebDriverWait(driver, 5)
    start_time = time.time()
    while time.time() - start_time < timeout_in_seconds:
        if graceful_exit.is_stop_requested():
            print('stop requested, exiting...')
            raise SystemExit(0)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "notes")))
            print('Challenge passed, continue...')
            return
        except TimeoutException:
            pass  # keep waiting
    raise ValueError(
        f'failed to pass the OpenReview challenge within '
        f'{timeout_in_seconds} seconds!')


def _refresh_clearance_token(driver):
    """
    the Cloudflare clearance token is valid for a limited time (~10
    minutes); once it expires, all requests return HTTP 403. Reload the
    page in a NEW tab and pass the challenge again to get a fresh token,
    without touching the current tab's DOM (the paper divs would become
    stale if the current page were reloaded).
    :param driver: selenium webdriver
    :return: None
    """
    current_handle = driver.current_window_handle
    url = driver.current_url
    driver.switch_to.new_window('tab')
    try:
        driver.get(url)
        wait_until_pass_challenge(driver)
    finally:
        driver.close()
        driver.switch_to.window(current_handle)


def _download_pdf_via_browser(driver, url, save_path):
    """
    download a file through the browser's own network stack (live cookies
    and the same TLS fingerprint as the browser session). python requests
    gets HTTP 403 from Cloudflare when the clearance token was issued by an
    interactive challenge or has been refreshed after the cookies were
    captured, while the browser itself always carries the latest token.
    Writes to "{save_path}.part" first and renames on success, so that an
    interrupted download never leaves a half-written file behind.
    :param driver: selenium webdriver
    :param url: str, file url
    :param save_path: str, full path to save the file
    :return: (bool, str|None), (True, None) on success, or
        (False, error_message)
    """
    head, tail = os.path.split(save_path)
    if head:
        os.makedirs(head, exist_ok=True)
    part_path = save_path + '.part'
    if os.path.exists(part_path):
        os.remove(part_path)
    script = """
        const [url, done] = arguments;
        fetch(url, {credentials: 'include'})
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                const ct = r.headers.get('content-type') || '';
                if (ct.includes('json') || ct.includes('html')) {
                    throw new Error('error page: ' + ct);
                }
                return r.blob();
            })
            .then(blob => new Promise((resolve, reject) => {
                const fr = new FileReader();
                fr.onload = () => resolve(fr.result);
                fr.onerror = reject;
                fr.readAsDataURL(blob);
            }))
            .then(dataUrl => {
                window.__openreview_dl = dataUrl.split(',')[1];
                done(window.__openreview_dl.length);
            })
            .catch(err => done('ERR:' + err.message));
    """
    max_retry_time = 5
    refresh_count = 0
    timeout_retry_count = 0
    for retry in range(max_retry_time):
        try:
            result = driver.execute_async_script(script, url)
        except TimeoutException:
            # the download took longer than the script timeout, retry it
            # (up to 2 times) in case the connection was just slow
            timeout_retry_count += 1
            if timeout_retry_count > 2:
                return False, 'script timeout (the download is too slow)'
            print(f'[script timeout] retrying {shorten_title(tail)} '
                  f'({timeout_retry_count}/2)...')
            time.sleep(5)
            continue
        if isinstance(result, str) and result.startswith('ERR:'):
            err_msg = result[4:]
            if '429' in err_msg and retry + 1 < max_retry_time:
                # OpenReview rate limits the API to 5 requests per ~17
                # seconds, wait until the limit resets and retry
                m = re.search(r'in (\d+) seconds', err_msg)
                wait = int(m.group(1)) + 5 if m else 30
                print(f'[429 rate limited] retrying {shorten_title(tail)} '
                      f'in {wait} seconds ({retry + 1}/{max_retry_time})...')
                time.sleep(wait)
                continue
            if '403' in err_msg and refresh_count < 2:
                # the clearance token has expired (valid ~10 minutes),
                # refresh it in a new tab and retry
                refresh_count += 1
                print(f'[HTTP 403] refreshing the Cloudflare clearance '
                      f'token ({refresh_count}/2) and retrying '
                      f'{shorten_title(tail)}...')
                _refresh_clearance_token(driver)
                continue
            return False, err_msg
        try:
            b64_len = int(result)
            # read the base64 string back in chunks to avoid huge webdriver
            # messages; chunk sizes are multiples of 4 so base64 decoding
            # never splits a unit
            offset = 0
            chunk = 1024 * 1024
            with open(part_path, 'wb') as f:
                while offset < b64_len:
                    part = driver.execute_script(
                        'return window.__openreview_dl.substring('
                        'arguments[0], arguments[1]);',
                        offset, min(offset + chunk, b64_len))
                    if part == '':
                        break
                    f.write(base64.b64decode(part))
                    offset += len(part)
            if offset < b64_len:
                return False, 'browser download incomplete'
            os.replace(part_path, save_path)
            return True, None
        finally:
            driver.execute_script('delete window.__openreview_dl;')
    return False, f'rate limited after {max_retry_time} retries'


def __download_papers_given_divs(driver, divs, save_dir, paper_postfix,
                                 time_step_in_seconds=10, downloader='IDM',
                                 proxy_ip_port=None):
    error_log = []
    downloader = Downloader(downloader=downloader, proxy_ip_port=proxy_ip_port)
    # the OpenReview website now requires the Cloudflare challenge/login
    # cookies for all requests, so forward the browser cookies to the
    # downloader (only used by the None|"request" downloader; IDM cannot
    # send cookies and will be rejected with 403)
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}

    # scroll to top of page
    # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
    driver.find_element(By.TAG_NAME, 'body').send_keys(
        Keys.CONTROL + Keys.HOME)
    time.sleep(0.3)

    # titles = [d.text for d in divs]
    titles = []
    for d in divs:
        for i in range(3):  # temp workaround
            try:
                titles.append(d.text)    
                break
            except Exception as e:
                if i == 2:
                    print(f'\tget Exception: {str(e)}')
                time.sleep(0.3)
                       
    valid_divs = []
    for i, t in enumerate(titles):
        if len(t):
            valid_divs.append(divs[i])
    num_papers = len(valid_divs)
    print('found number of papers:', num_papers)
    name = None
    for index, paper in enumerate(valid_divs):
        if graceful_exit.is_stop_requested():
            print('stop requested, stop downloading new papers...')
            break
        is_get_paper = False
        try:
            a_hrefs = paper.find_elements(By.TAG_NAME, "a")
            name = slugify(a_hrefs[0].text.strip())
            if a_hrefs[1].get_attribute('class') == 'pdf-link':
                # has pdf button
                link = a_hrefs[1].get_attribute('href')
                link = urllib.parse.urljoin('https://openreview.net', link)
            else:
                # raise ValueError('pdf link not found!')
                print('\tWarning: pdf link not found, skip this download...')
                if name is not None:
                    error_log.append((name, str(index)))
                else:
                    error_log.append((str(index), str(index)))
                continue
                # TODO: find pdf link in paper abstract page
            if name == '':
                continue
            is_get_paper = True
        except Exception as e:
            print(f'\tget Exception: {str(e)}')
            print('\tskip this download...')
            if name is not None:
                error_log.append((name, str(index)))
            else:
                error_log.append((str(index), str(index)))
        if not is_get_paper:
            continue

        # name = slugify(paper.find_element_by_class_name('note_content_title').text)
        # link = paper.find_element_by_class_name('note_content_pdf').get_attribute('href')
        pdf_name = name + '_' + paper_postfix + '.pdf'
        # also re-download suspiciously small files left by previous failed
        # runs (e.g. the 287-byte rate-limit error pages)
        if not is_valid_downloaded_file(os.path.join(save_dir, pdf_name)):
            print('Downloading paper {}/{}: {}'.format(index + 1, num_papers,
                                                       shorten_title(name)))
            # get pdf link of arxiv if the original link is on arxiv.org
            if "arxiv.org/abs" in link:
                link = get_pdf_link_from_arxiv(abs_link=link)
            # try 1 times
            success_flag = False
            if downloader.downloader is None:
                # download through the browser's own network stack, which
                # always carries the live clearance cookies; python
                # requests gets HTTP 403 once the clearance token has been
                # refreshed by a new challenge after the cookies were
                # captured
                this_save_path = os.path.join(save_dir, pdf_name)
                try:
                    success_flag, err_msg = _download_pdf_via_browser(
                        driver, link, this_save_path)
                except Exception as e:
                    success_flag, err_msg = False, str(e)
                if success_flag:
                    size = os.path.getsize(this_save_path)
                    print(f'\tdownloaded {shorten_title(name)}_'
                          f'{paper_postfix}.pdf '
                          f'({round(size / 1024)} KB)')
                else:
                    print(f'Error: {shorten_title(name)} - {err_msg}')
                # pace the interval between two download requests with the
                # given time_step_in_seconds (randomly sampled 0.5t~1.5t,
                # same as the requests path), to stay under the OpenReview
                # API rate limit of 5 requests per ~17 seconds
                step = time_step_in_seconds
                if downloader.is_random_step:
                    step = random.uniform(
                        0.5 * time_step_in_seconds,
                        1.5 * time_step_in_seconds)
                time.sleep(step)
            else:
                for d_iter in range(1):
                    try:
                        downloader.download(
                            urls=link,
                            save_path=os.path.join(save_dir, pdf_name),
                            time_sleep_in_seconds=time_step_in_seconds,
                            cookies=cookies
                        )
                        success_flag = True
                        break
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
            if not success_flag:
                error_log.append((name, link))
    return error_log, num_papers


def __get_into_pages_given_number(driver, page_number, pages, wait_fn,
                                  condition=None, pages_xpath=None):
    """
    navigate to the page with the given number: click it directly if it is
    visible in the pagination bar; otherwise, since the bar only shows a
    ~10-page window around the current page (the 2026 UI), jump the window
    forward via its highest visible page number (or flip one page with the
    "›" button when the window cannot advance) until the target page
    becomes visible, then click it.
    :param driver: selenium webdriver
    :param page_number: int, the page number to navigate to
    :param pages: list[WebElement], the pagination bar's li elements
    :param wait_fn: callable, the wait function to call after navigation
    :param condition: str or None, extra condition passed to wait_fn
    :param pages_xpath: str or None, xpath of the pagination bar's li
        elements, used to re-read the bar after each navigation; None
        disables the flip-forward fallback (the target must be visible)
    :return: the clicked li element, or None if the target page cannot be
        reached
    """
    wait_fn(driver, condition)
    for page in pages:
        if page.text.isnumeric() and int(page.text) == page_number:
            page_link = page.find_element(By.TAG_NAME, "a")
            page_link.click()
            wait_fn(driver, condition)
            return page
    if pages_xpath is None:
        return None
    # the target page is not in the visible window, flip forward
    last_active = None
    for _ in range(page_number + 10):
        dom_page = _get_current_page_from_dom(driver, pages_xpath)
        if dom_page is not None and dom_page == last_active:
            return None  # the page did not advance, give up
        if dom_page is not None:
            last_active = dom_page
        numbers = [int(li.text) for li in pages if li.text.isnumeric()]
        if not numbers:
            return None
        if page_number in numbers:
            # the target page is visible now, click it directly
            for page in pages:
                if page.text.isnumeric() and int(page.text) == page_number:
                    page_link = page.find_element(By.TAG_NAME, "a")
                    page_link.click()
                    wait_fn(driver, condition)
                    return page
        # jump the window forward via its highest visible page number, or
        # flip one page with the "›" button if the window cannot advance
        jump_to = numbers[-1] if numbers[-1] > (dom_page or 0) else None
        next_button = None
        for li in pages:
            if '›' in li.text:
                next_button = li
                break
        try:
            if jump_to is not None and jump_to < page_number:
                for li in pages:
                    if li.text.isnumeric() and int(li.text) == jump_to:
                        driver.execute_script(
                            'arguments[0].click()',
                            li.find_element(By.TAG_NAME, 'a'))
                        break
            elif next_button is not None:
                driver.execute_script(
                    'arguments[0].click()',
                    next_button.find_element(By.TAG_NAME, 'a'))
            else:
                return None
        except Exception:
            return None
        wait_fn(driver, condition)
        pages = driver.find_elements(By.XPATH, pages_xpath)
    return None


def _get_current_page_from_dom(driver, pages_xpath):
    """
    the page number the browser is currently showing, read from the
    highlighted (active) button of the pagination bar. The DOM is the source
    of truth: after a Cloudflare challenge, or when mywait re-clicks the
    group tab because the panel was hidden, the panel can re-render from
    the first page while the in-memory counter keeps counting, making every
    later page offset and silently skipping the last pages.
    :param driver: selenium webdriver
    :param pages_xpath: str, xpath of the pagination bar's li elements
    :return: int or None (if the active page can not be read)
    """
    try:
        lis = driver.find_elements(By.XPATH, pages_xpath)
        for li in lis:
            cls = li.get_attribute('class') or ''
            if 'active' in cls or 'selected' in cls:
                text = li.find_element(By.TAG_NAME, 'a').text
                if text.isnumeric():
                    return int(text)
    except Exception:
        pass
    return None


def _sync_current_page(driver, pages_xpath, current_page):
    """
    re-sync the in-memory page counter with the page the browser is actually
    showing, and warn if they have drifted
    :param driver: selenium webdriver
    :param pages_xpath: str, xpath of the pagination bar's li elements
    :param current_page: int, the in-memory page counter
    :return: int, the page number read from the DOM (or the given counter
        if it can not be read)
    """
    dom_page = _get_current_page_from_dom(driver, pages_xpath)
    if dom_page is not None and dom_page != current_page:
        print(f'[page re-sync] the browser shows page {dom_page} instead of '
              f'{current_page}, continuing from there...')
    if dom_page is None:
        return current_page
    return dom_page


def download_nips_papers_given_url(
        save_dir, year, base_url, conference='NIPS', start_page=1,
        time_step_in_seconds=10, download_groups='all', downloader='IDM',
        proxy_ip_port=None):
    """
    download NeurIPS papers from the given web url.
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param conference: str, conference name, such as NIPS.
    :param start_page: int, the initial downloading webpage number, only the pages whose number is
                            equal to or greater than this number will be processed.
    :param time_step_in_seconds: int, the interval time between two downlaod request in seconds
    :param groups: group name, such as 'oral', 'spotlight', 'poster'.
        Default: 'all'.
    :type download_groups: str | list[str]
    :param downloader: str, the downloader to download, could be 'IDM' or None,
        default to 'IDM'
    :param proxy_ip_port: str or None, proxy server ip address with or without
        protocol prefix, eg: "127.0.0.1:7890", "http://127.0.0.1:7890".
        (only useful for None|"request" downloader and webdriver)
        Default: None
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if year < 2023:
        sub_xpath = '''id="accepted-papers"'''
    else:
        sub_xpath = '''class="submissions-list"'''
    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        # res = wait.until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "note")))
        res = wait.until(
            EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website notes!->", res)
        res = wait.until(EC.presence_of_element_located(
            (By.XPATH, f'''//*[@{sub_xpath}]/nav''')))
        # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    def find_divs_of_papers():
        if year < 2023:
            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')
        else:
            # divs = driver.find_element(By.ID, group_id). \
            #     find_elements(By.XPATH, '//*[@class="note  undefined"]')
            divs = driver.find_element(By.ID, group_id).find_elements(
                By.XPATH, 
                '//*[contains(@class, "note") and contains(@class, "undefined")]'
            )
        return divs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    # do not launch a new browser after the first Ctrl+C
    if graceful_exit.is_stop_requested():
        print('stop requested, skip this group...')
        return
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)
    wait_until_pass_challenge(driver)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    mywait(driver)
    # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')

    # download grouped papers, such as "Accepted Papaers" for year before 2023
    # "Accept (oral)", "Accept (spotlight)", "Accept (poster)" for year 2023
    groups = driver.find_elements(
        By.XPATH, f'//*[@id="notes"]/div/div[1]/ul/li')
    accept_groups = []
    for g in groups:
        if 'accept' in g.text.lower():
            # whether download this group
            is_download_group = True
            if not 'all' == download_groups:
                is_download_group = False
                for dg in download_groups:
                    if dg.lower() in g.text.lower():
                        is_download_group = True
                        break
            if is_download_group:
                accept_groups.append(g)
    group_name = None
    group_save_dir = save_dir
    for ag in accept_groups:
        group_name = slugify(ag.text)
        group_save_dir = os.path.join(save_dir, group_name)
        print(f'Downloading {group_name}...')
        os.makedirs(group_save_dir, exist_ok=True)
        number_paper_group = 0
        accept_group_link = ag.find_element(By.TAG_NAME, "a")
        # group_id = accept_group_link.get_attribute('aria-controls')
        group_id = accept_group_link.get_attribute('href').split('#')[-1]
        # scroll to top of page, if not at top, the click action not work
        # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        time.sleep(0.2)
        accept_group_link.click()
        mywait(driver)
        pages = driver.find_elements(
            By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
        page_str_list = get_pages_str(pages)
        # print(f'Current page navigation bar:\n{page_str_list}')
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        # << | < | 1, 2, 3, ... | > | >>
        total_pages_number = get_max_page_number(page_str_list)
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            if total_pages_number < start_page:  # flip pages until seeing the start page
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait,
                    pages_xpath=f'//*[@{sub_xpath}]/nav[1]/ul/li')
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, '//*[@id="accepted-papers"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, '''//*[@id="accepted-papers"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')
                pages = pages = driver.find_elements(
                    By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
                page_str_list = get_pages_str(pages)
                total_pages_number = get_max_page_number(page_str_list)
                # # print(f'Current page navigation bar:\n{page_str_list}')
                if total_pages_number == last_total_pages:  # total page remain unchanged after reload
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till less than start page, so
                    # the start page doesn't exist. PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages,
            wait_fn=mywait,
            pages_xpath=f'//*[@{sub_xpath}]/nav[1]/ul/li')

        while current_page <= total_pages_number:
            if page is None:
                break
            if graceful_exit.is_stop_requested():
                print('stop requested, stop downloading new pages...')
                break
            print(f'downloading papers in page: {current_page}')
            _force_gc(driver)
            mywait(driver)

            # divs = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/ul/li')
            # divs = driver.find_elements(By.XPATH, '//*[@id="accepted-papers"]/ul/li')
            divs = find_divs_of_papers()

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = find_divs_of_papers()
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=group_save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            number_paper_group += this_number_paper
            # do not make any more webdriver calls after the first Ctrl+C
            if graceful_exit.is_stop_requested():
                break
            # get into next page
            current_page += 1
            # pages = driver.find_elements_by_xpath('//*[@id="accepted-papers"]/nav/ul/li')
            pages = driver.find_elements(
                By.XPATH, f'//*[@{sub_xpath}]/nav[1]/ul/li')
            page_str_list = get_pages_str(pages)
            total_pages_number = get_max_page_number(page_str_list)
            # print(f'Current page navigation bar:\n{page_str_list}')
            # if we do not reread the pages, all the pages will be not available with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the page document
            page = __get_into_pages_given_number(driver=driver,
                                                 page_number=current_page,
                                                 pages=pages,
                                                 wait_fn=mywait,
                                                 pages_xpath=f'//*[@{sub_xpath}]/nav[1]/ul/li')
            current_page = _sync_current_page(
                driver, f'//*[@{sub_xpath}]/nav[1]/ul/li', current_page)
        # display total number of papers
        print(f'number of papers in {group_name}: {number_paper_group}')

    try:
        driver.quit()
    except Exception:
        pass  # the webdriver may have already died from the first Ctrl+C
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_iclr_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference='ICLR', start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None,
        is_have_pages=True, is_need_click_group_button=False):
    """
    downlaod ICLR papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "notable-top-5-",
        "notable-top-25-", "poster", "oral-submissions",
        "spotlight-submissions", "poster-submissions", etc.
    :type group_id: str
    :param conference: str, conference name, such as ICLR. Default: ICLR
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890".  Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :param is_have_pages: bool, is there pages in webpage. Default:
        True.
    :type is_have_pages: bool
    :param is_need_click_group_button: bool, is there need to click the
        group button in webpage. For some years, for example 2018, the
        navigation part "#xxxxx" in base url will not work. And it should
        be clicked before reading content from webpage. Default: False.
    :type is_need_click_group_button: bool
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def _get_pages_xpath(year):
        if year <= 2023:
            xpath = f'''//*[@id="{group_id}"]/nav/ul/li'''
        else:
            xpath = f'''//*[@id="{group_id}"]/div/div/nav/ul/li'''
        return xpath

    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        if year <= 2023:
            res = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "note")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        if is_have_pages:
            # scroll to bottom of page
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.END)
            if year <= 2023:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            else:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    # do not launch a new browser after the first Ctrl+C
    if graceful_exit.is_stop_requested():
        print('stop requested, skip this group...')
        return
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)
    wait_until_pass_challenge(driver)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if is_need_click_group_button:
        archive_is_have_pages = is_have_pages
        is_have_pages = False
        mywait(driver)
        aria_controls = base_url.split('#')[-1]
        # scroll to home of page
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        group_button = driver.find_element(
            By.XPATH, f"""//a[@aria-controls="{aria_controls}"]"""
        )
        group_button.click()
        is_have_pages = archive_is_have_pages
    mywait(driver)
    if is_have_pages:
        pages = driver.find_elements(By.XPATH, _get_pages_xpath(year))
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        total_pages_number = int(pages[-3].text)
        # << | < | 1, 2, 3, ... | > | >>
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            # flip pages until seeing the start page
            if total_pages_number < start_page:
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait,
                    pages_xpath=_get_pages_xpath(year))
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'//*[@id="{group_id}"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                pages = driver.find_elements(
                    By.XPATH, _get_pages_xpath(year))
                total_pages_number = int(pages[-3].text)
                # total page remain unchanged after reload
                if total_pages_number == last_total_pages:
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till
                    # less than start page, so the start page doesn't exist.
                    # PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages,
            wait_fn=mywait, pages_xpath=_get_pages_xpath(year))

        while current_page <= total_pages_number:
            if page is None:
                break
            if graceful_exit.is_stop_requested():
                print('stop requested, stop downloading new pages...')
                break
            print(f'downloading {group_id} papers in page: {current_page}')
            _force_gc(driver)
            mywait(driver)

            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = driver.find_element(By.ID, group_id). \
                            find_elements(By.CLASS_NAME, 'note ')
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            # do not make any more webdriver calls after the first Ctrl+C
            if graceful_exit.is_stop_requested():
                break
            # get into next page
            current_page += 1
            pages = driver.find_elements(
                By.XPATH, _get_pages_xpath(year))
            total_pages_number = int(pages[-3].text)
            # if we do not reread the pages, all the pages will be not available
            # with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the
            # page document
            page = __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait, pages_xpath=_get_pages_xpath(year))
            current_page = _sync_current_page(
                driver, _get_pages_xpath(year), current_page)
    else:  # no pages
        divs = driver.find_element(By.ID, group_id). \
            find_elements(By.CLASS_NAME, 'note ')
        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r + 1) < repeat_times:
                    print(f'\terror occurre: {str(e)}')
                    print(f'\tsleep {(r + 1) * 5} seconds...')
                    time.sleep((r + 1) * 5)
                    print(f'{r + 1}-th reloading page')
                    divs = driver.find_element(By.ID, group_id). \
                        find_elements(By.CLASS_NAME, 'note ')
                else:
                    print('\tskipped!!!')
        if is_find_paper:
            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)

    try:
        driver.quit()
    except Exception:
        pass  # the webdriver may have already died from the first Ctrl+C
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def download_icml_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference='ICML', start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None):
    """
    downlaod ICLR papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "poster" and "oral".
    :type group_id: str
    :param conference: str, conference name, such as ICLR. Default: ICLR
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890". Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def mywait(driver, aria_controls=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        wait = WebDriverWait(driver, 20)
        # ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        res = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "submissions-list")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        # scroll to bottom of page
        # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.END)
        time.sleep(0.3)
        if aria_controls is None:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f'//*[@class="submissions-list"]/nav/ul/li[3]/a''')))
        else:
            # the panel is rendered lazily and the page occasionally fails
            # to switch to the clicked group tab (or switches back to the
            # first tab later), which hides the panel and makes its
            # pagination unclickable; wait for the panel to render first,
            # and re-click the group's tab only if it stays hidden.
            # NOTE: clicking the tab re-renders the panel from the first
            # page (losing the current page), so first try to reveal the
            # panel by scrolling, which does not reset the pagination.
            wait.until(EC.presence_of_element_located(
                (By.ID, aria_controls)))
            for _ in range(3):
                if driver.find_element(
                        By.ID, aria_controls).is_displayed():
                    break
                print(f'the {aria_controls} panel is hidden, '
                      f're-clicking its tab...')
                # scroll to the bottom to trigger the lazy rendering of
                # the panel content
                driver.find_element(By.TAG_NAME, 'body').send_keys(
                    Keys.CONTROL + Keys.END)
                time.sleep(2)
                if driver.find_element(
                        By.ID, aria_controls).is_displayed():
                    break
                for li in driver.find_elements(
                        By.XPATH, '//ul[@class="nav nav-tabs"]/li'):
                    link = li.find_element(By.TAG_NAME, 'a')
                    href = link.get_attribute('href')
                    if href is not None and \
                            href.split('#')[-1] == aria_controls:
                        link.click()
                        break
                driver.find_element(By.TAG_NAME, 'body').send_keys(
                    Keys.CONTROL + Keys.END)
                time.sleep(1)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 f'''//*[@id='{aria_controls}']/div/div/nav/ul/li[3]/a''')))
            wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 f'''//*[@id='{aria_controls}']/div/div/ul/li[1]/div/h4/a[1]''')))
        # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []
    # do not launch a new browser after the first Ctrl+C
    if graceful_exit.is_stop_requested():
        print('stop requested, skip this group...')
        return
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)
    wait_until_pass_challenge(driver)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # wait = WebDriverWait(driver, 20)
    mywait(driver)

    # get into poster or oral page
    nav_tap = driver.find_elements(
        By.XPATH, f'//ul[@class="nav nav-tabs"]/li')
    is_found_group = False
    for li in nav_tap:
        if group_id in li.text.lower():
            if 'poster' in group_id and 'spotlight' in li.text.lower():
                # spotlight-poster should be recognized as spotlight rather
                # than poster
                continue
            page_link = li.find_element(By.TAG_NAME, "a")
            # scroll to top of page, if not at top, the click action not work
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.HOME)
            # the new UI (since 2026) has no aria-controls attribute on the
            # tab links; the panel id is the hash of the link's href, e.g.
            # "accept-spotlight"
            aria_controls = page_link.get_attribute('aria-controls')
            if aria_controls is None:
                aria_controls = page_link.get_attribute('href').split('#')[-1]
            page_link.click()
            mywait(driver, aria_controls)  # there is no request in here
            is_found_group = True
            break
    if not is_found_group:
        raise ValueError(f'not found {group_id} papers at {base_url}!!!')

    # pages = driver.find_elements(
    #     By.XPATH, f'//nav[@aria-label="page navigation"]/ul/li')
    pages = driver.find_elements(
        By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
    current_page = 1
    # ind_page = 2  # 0 << ; 1 <
    # the pagination bar only shows a ~10-page window around the current
    # page, so the last page number in the bar is NOT the total number of
    # pages; reveal the real total by clicking the "»" (last page) button
    # once, then go back to the first page
    last_button = pages[-1]
    if '»' in last_button.text:
        driver.execute_script(
            'arguments[0].click()',
            last_button.find_element(By.TAG_NAME, 'a'))
        mywait(driver, aria_controls)
        pages = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
        total_pages_number = int(pages[-3].text)  # the real total
        # go back to the first page
        first_button = pages[0]
        driver.execute_script(
            'arguments[0].click()',
            first_button.find_element(By.TAG_NAME, 'a'))
        mywait(driver, aria_controls)
        pages = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
    else:
        total_pages_number = int(pages[-3].text)
    last_total_pages = total_pages_number
    # get into start pages
    while current_page < start_page:
        # flip pages until seeing the start page
        if total_pages_number < start_page:
            current_page = total_pages_number
            __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait, condition=aria_controls,
                pages_xpath=f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
            print(f'getting into web page {current_page}...')

            # print("Successful load the website pagination!->", res)
            pages = driver.find_elements(
                By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
            total_pages_number = int(pages[-3].text)
            # total page remain unchanged after reload
            if total_pages_number == last_total_pages:
                print(f'reached last({total_pages_number}-th) webpage')
                # when get the last page, but the page number is till less than
                # start page, so the start page doesn't exist. PRINT ERROR and
                # return
                print(f'ERROR: THE {start_page}-th webpage not found!')
                return
        else:
            current_page = start_page

    page = __get_into_pages_given_number(
        driver=driver, page_number=current_page, pages=pages, wait_fn=mywait,
        condition=aria_controls,
        pages_xpath=f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
    current_page = _sync_current_page(
        driver, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''',
        current_page)

    while current_page <= total_pages_number:
        if page is None:
            break
        if graceful_exit.is_stop_requested():
            print('stop requested, stop downloading new pages...')
            break
        print(f'downloading {group_id} papers in page: {current_page}')
        _force_gc(driver)

        # the note list is rendered by JS after the page data is fetched,
        # wait for the first paper element so a transient slow/failed fetch
        # does not make the page look empty
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     f'''//*[@id='{aria_controls}']/div/div/ul/li''')))
        except TimeoutException:
            pass
        divs = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/ul/li''')

        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r+1) < repeat_times:
                    print(f'\terror occurre: {str(e)}')
                    print(f'\tsleep {(r+1)*5} seconds...')
                    time.sleep((r+1)*5)
                    print(f'{r+1}-th reloading page')
                    divs = driver.find_elements(
                        By.XPATH,
                        f'''//*[@id='{aria_controls}']/div/div/ul/li''')
                else:
                    print('\tskip this page.')
        if not is_find_paper:
            continue
        # time.sleep(time_step_in_seconds)
        this_error_log, this_number_paper = __download_papers_given_divs(
            driver=driver,
            divs=divs,
            save_dir=save_dir,
            paper_postfix=paper_postfix,
            time_step_in_seconds=time_step_in_seconds,
            downloader=downloader,
            proxy_ip_port=proxy_ip_port
        )
        for e in this_error_log:
            error_log.append(e)
        # do not make any more webdriver calls after the first Ctrl+C
        if graceful_exit.is_stop_requested():
            break
        # get into next page via the "›" (next page) button, since the
        # pagination bar only shows a ~10-page window and the target page
        # number may not be in it; total_pages_number was revealed at the
        # start by clicking the "»" button, so do NOT re-read it here
        current_page += 1
        if current_page > total_pages_number:
            page = None
            break
        intended_page = current_page
        pages = driver.find_elements(
            By.XPATH, f'''//*[@id='{aria_controls}']/div/div/nav/ul/li''')
        next_button = None
        for li in pages:
            if '›' in li.text:
                next_button = li
                break
        if next_button is None:
            page = None
            break
        try:
            driver.execute_script(
                'arguments[0].click()',
                next_button.find_element(By.TAG_NAME, 'a'))
        except Exception:
            page = None
            break
        mywait(driver, aria_controls)
        # the DOM is the source of truth: a Cloudflare challenge or the
        # hidden-panel tab re-click can re-render the panel from the first
        # page while the counter keeps counting; re-sync it here, otherwise
        # every later page would be offset and the last pages skipped
        pages_xpath = f'''//*[@id='{aria_controls}']/div/div/nav/ul/li'''
        current_page = _sync_current_page(driver, pages_xpath, current_page)
        if current_page < intended_page:
            # the panel was re-rendered from an earlier page (e.g. after
            # the hidden-panel tab re-click): jump forward to the intended
            # page instead of re-processing the already-done pages
            print(f'jumping back to page {intended_page}...')
            pages = driver.find_elements(By.XPATH, pages_xpath)
            __get_into_pages_given_number(
                driver=driver, page_number=intended_page, pages=pages,
                wait_fn=mywait, condition=aria_controls,
                pages_xpath=pages_xpath)
            current_page = _sync_current_page(driver, pages_xpath,
                                              current_page)
        page = next_button

    try:
        driver.quit()
    except Exception:
        pass  # the webdriver may have already died from the first Ctrl+C
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')


def get_pages_str(pages):
    page_str_list = [p.text for p in pages]
    # print(f'Current page navigation bar:\n{page_str_list}')
    return page_str_list


def get_max_page_number(page_str_list):
    is_find_number = False
    for i, page_str in enumerate(page_str_list):
        if not page_str.isnumeric() and is_find_number:
            return int(page_str_list[i-1])
        if page_str.isnumeric():
            is_find_number = True
    return int(page_str_list[-1])


def download_papers_given_url_and_group_id(
        save_dir, year, base_url, group_id, conference, start_page=1,
        time_step_in_seconds=10, downloader='IDM', proxy_ip_port=None,
        is_have_pages=True, is_need_click_group_button=False):
    """
    downlaod papers for the given web url and the paper group id
    :param save_dir: str, paper save path
    :type save_dir: str
    :param year: int, iclr year, current only support year >= 2018
    :type year: int
    :param base_url: str, paper website url
    :type base_url: str
    :param group_id: str, paper group id, such as "notable-top-5-",
        "notable-top-25-", "poster", "oral-submissions",
        "spotlight-submissions", "poster-submissions", etc.
    :type group_id: str
    :param conference: str, conference name, such as CORL.
    :param start_page: int, the initial downloading webpage number, only the
        pages whose number is equal to or greater than this number will be
        processed. Default: 1
    :param time_step_in_seconds: int, the interval time between two download
        request in seconds. Default: 10
    :param downloader: str, the downloader to download, could be 'IDM' or
        'Thunder'. Default: 'IDM'
    :param proxy_ip_port: str or None, proxy ip address and port, eg.
        eg: "127.0.0.1:7890".  Only useful for webdriver and request
        downloader (downloader=None). Default: None.
    :type proxy_ip_port: str | None
    :param is_have_pages: bool, is there pages in webpage. Default:
        True.
    :type is_have_pages: bool
    :param is_need_click_group_button: bool, is there need to click the
        group button in webpage. For some years, for example 2018, the
        navigation part "#xxxxx" in base url will not work. And it should
        be clicked before reading content from webpage. Default: False.
    :type is_need_click_group_button: bool
    :return:
    """
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def _get_pages_xpath(year):
        if year <= 2023:
            xpath = f'''//*[@id="{group_id}"]/nav/ul/li'''
        else:
            xpath = f'''//*[@id="{group_id}"]/div/div/nav/ul/li'''
        return xpath

    def mywait(driver, condition=None):
        # wait for the select element to become visible
        # print('Starting web driver wait...')
        # ignored_exceptions = (NoSuchElementException, 
        # StaleElementReferenceException,)
        # wait = WebDriverWait(driver, 20, ignored_exceptions=ignored_exceptions)
        wait = WebDriverWait(driver, 20)
        # print('Starting web driver wait... finished')
        # res = wait.until(EC.presence_of_element_located((By.ID, "notes")))
        # print("Successful load the website!->", res)
        # if year <= 2023:
        #     res = wait.until(
        #         EC.presence_of_element_located((By.CLASS_NAME, "note")))
        # print("Successful load the website notes!->", res)
        # res = wait.until(EC.presence_of_element_located(
        #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
        if is_have_pages:
            # scroll to bottom of page
            # https://stackoverflow.com/questions/45576958/scrolling-to-top-of-the-page-in-python-using-selenium
            driver.find_element(By.TAG_NAME, 'body').send_keys(
                Keys.CONTROL + Keys.END)
            if year <= 2023:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            else:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'{_get_pages_xpath(year)}[3]/a')))
            # print("Successful load the website pagination!->", res)
        time.sleep(2)  # seconds, workaround for bugs

    paper_postfix = f'{conference}_{year}'
    error_log = []

    # do not launch a new browser after the first Ctrl+C
    if graceful_exit.is_stop_requested():
        print('stop requested, skip this group...')
        return
    driver = get_driver(proxy_ip_port=proxy_ip_port)
    driver.get(base_url)
    wait_until_pass_challenge(driver)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if is_need_click_group_button:
        archive_is_have_pages = is_have_pages
        is_have_pages = False
        mywait(driver)
        aria_controls = base_url.split('#')[-1]
        # scroll to home of page
        driver.find_element(By.TAG_NAME, 'body').send_keys(
            Keys.CONTROL + Keys.HOME)
        group_button = driver.find_element(
            By.XPATH, f"""//a[@aria-controls="{aria_controls}"]"""
        )
        group_button.click()
        is_have_pages = archive_is_have_pages
    mywait(driver)
    if is_have_pages:
        pages = driver.find_elements(By.XPATH, _get_pages_xpath(year))
        current_page = 1
        ind_page = 2  # 0 << ; 1 <
        total_pages_number = int(pages[-3].text)
        # << | < | 1, 2, 3, ... | > | >>
        last_total_pages = total_pages_number
        # get into start pages
        while current_page < start_page:
            # flip pages until seeing the start page
            if total_pages_number < start_page:
                current_page = total_pages_number
                __get_into_pages_given_number(
                    driver=driver, page_number=current_page, pages=pages,
                    wait_fn=mywait,
                    pages_xpath=_get_pages_xpath(year))
                print(f'getting into web page {current_page}...')
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'//*[@id="{group_id}"]/ul/li/h4/a')))
                # res = wait.until(EC.presence_of_element_located(
                #     (By.XPATH, f'''//*[@id="{group_id}"]/nav''')))
                mywait(driver)

                # print("Successful load the website pagination!->", res)
                pages = driver.find_elements(
                    By.XPATH, _get_pages_xpath(year))
                total_pages_number = int(pages[-3].text)
                # total page remain unchanged after reload
                if total_pages_number == last_total_pages:
                    print(f'reached last({total_pages_number}-th) webpage')
                    # when get the last page, but the page number is till
                    # less than start page, so the start page doesn't exist.
                    # PRINT ERROR and return
                    print(f'ERROR: THE {start_page}-th webpage not found!')
                    return
            else:
                current_page = start_page

        page = __get_into_pages_given_number(
            driver=driver, page_number=current_page, pages=pages,
            wait_fn=mywait, pages_xpath=_get_pages_xpath(year))

        while current_page <= total_pages_number:
            if page is None:
                break
            if graceful_exit.is_stop_requested():
                print('stop requested, stop downloading new pages...')
                break
            print(f'downloading {group_id} papers in page: {current_page}')
            _force_gc(driver)
            mywait(driver)

            divs = driver.find_element(By.ID, group_id). \
                find_elements(By.CLASS_NAME, 'note ')

            # temp workaround
            repeat_times = 3
            is_find_paper = False
            for r in range(repeat_times):
                try:
                    a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                    name = slugify(a_hrefs[0].text.strip())
                    link = a_hrefs[1].get_attribute('href')
                    is_find_paper = True
                    break
                except Exception as e:
                    if (r + 1) < repeat_times:
                        print(f'\terror occurre: {str(e)}')
                        print(f'\tsleep {(r + 1) * 5} seconds...')
                        time.sleep((r + 1) * 5)
                        print(f'{r + 1}-th reloading page')
                        divs = driver.find_element(By.ID, group_id). \
                            find_elements(By.CLASS_NAME, 'note ')
                    else:
                        print('\tskip this page.')
            if not is_find_paper:
                continue

            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)
            # do not make any more webdriver calls after the first Ctrl+C
            if graceful_exit.is_stop_requested():
                break
            # get into next page
            current_page += 1
            pages = driver.find_elements(
                By.XPATH, _get_pages_xpath(year))
            total_pages_number = int(pages[-3].text)
            # if we do not reread the pages, all the pages will be not available
            # with an exception:
            # selenium.common.exceptions.StaleElementReferenceException:
            # Message: stale element reference: element is not attached to the
            # page document
            page = __get_into_pages_given_number(
                driver=driver, page_number=current_page, pages=pages,
                wait_fn=mywait, pages_xpath=_get_pages_xpath(year))
            current_page = _sync_current_page(
                driver, _get_pages_xpath(year), current_page)
    else:  # no pages
        divs = driver.find_element(By.ID, group_id). \
            find_elements(By.CLASS_NAME, 'note ')
        # temp workaround
        repeat_times = 3
        is_find_paper = False
        for r in range(repeat_times):
            try:
                a_hrefs = divs[0].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                a_hrefs = divs[-1].find_elements(By.TAG_NAME, "a")
                name = slugify(a_hrefs[0].text.strip())
                link = a_hrefs[1].get_attribute('href')
                is_find_paper = True
                break
            except Exception as e:
                if (r + 1) < repeat_times:
                    print(f'\terror occurre: {str(e)}')
                    print(f'\tsleep {(r + 1) * 5} seconds...')
                    time.sleep((r + 1) * 5)
                    print(f'{r + 1}-th reloading page')
                    divs = driver.find_element(By.ID, group_id). \
                        find_elements(By.CLASS_NAME, 'note ')
                else:
                    print('\tskipped!!!')
        if is_find_paper:
            # time.sleep(time_step_in_seconds)
            this_error_log, this_number_paper = __download_papers_given_divs(
                driver=driver,
                divs=divs,
                save_dir=save_dir,
                paper_postfix=paper_postfix,
                time_step_in_seconds=time_step_in_seconds,
                downloader=downloader,
                proxy_ip_port=proxy_ip_port
            )
            for e in this_error_log:
                error_log.append(e)

    try:
        driver.quit()
    except Exception:
        pass  # the webdriver may have already died from the first Ctrl+C
    # 2. write error log
    print('write error log')
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'download_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                f.write(e)
                f.write('\n')
            f.write('\n')



if __name__ == "__main__":
    year = 2023
    save_dir = rf'E:\ICML_{year}'
    base_url = 'https://openreview.net/group?id=ICML.cc/2023/Conference'
    # download_nips_papers_given_url(
    #     save_dir, year, base_url,
    #     start_page=1,
    #     time_step_in_seconds=10,
    #     downloader='IDM')
    # download_icml_papers_given_url_and_group_id(
    #     save_dir, year, base_url, group_id='oral', start_page=1,
    #     time_step_in_seconds=10, )
