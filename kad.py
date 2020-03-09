from datetime import datetime
from requests import get
from os import path, remove, rename
from subprocess import check_output, CalledProcessError
import re
import configparser


class Utils:

    @staticmethod
    def display_error_and_terminate(error_message):
        print(f'[{str(datetime.now()).split(".")[0]}]: Error - {error_message}')
        input("Press Enter to exit...")
        exit(1)

    @staticmethod
    def display_message(message):
        print(f'[{str(datetime.now()).split(".")[0]}]: {message}')


class Config:

    def __init__(self):
        if not path.exists('krita.config'):
            Utils.display_error_and_terminate('\'krita.config\' does not exist')

        self.__config__ = configparser.RawConfigParser()
        self.__config__.read('krita.config')

    def get(self, config_name, values_name):
        return self.__config__.get(config_name, values_name)


class Krita:
    __base_url__ = "https://binary-factory.kde.org/job/Krita_Nightly_Android_Build/"
    __latest__ = False

    app_name = 'org.krita'
    required_space = 1.5

    def __init__(self, file_path, version=''):
        if not version:
            self.__build_version__ = self.__get_latest_version_number__()
            self.__latest__ = True
        else:
            self.__build_version__ = version
            self.__latest__ = False

        if not file_path[-1] == '/' and file_path[-1] != '\\':
            file_path += '/'

        self.file_url = f'{file_path}krita_build_apk-release-{self.__build_version__}-unsigned.apk'
        self.__download_url__ = f'{self.__build_version__}/artifact/krita_build_apk-release-unsigned.apk'

    def __get_latest_version_number__(self):
        Utils.display_message('Checking latest version')

        res = get(self.__base_url__, verify=False)

        if res.status_code != 200:
            Utils.display_error_and_terminate(f'Version check failed, response status: {res.status_code}')

        res = str(res.content).split("\\n")
        for item in res:
            m = re.search(r'Last stable build \(#(\d+)\)', item)
            if m:
                latest_version = m.group(1)
                Utils.display_message(f'Latest version: {latest_version}')
                return latest_version
        Utils.display_error_and_terminate('Latest version was not found')

    def download(self):
        if path.exists(self.file_url) or path.exists(self.file_url.replace('-unsigned', '')):
            Utils.display_message('The current version is already downloaded')
        else:
            if not self.__latest__:
                latest_version = self.__get_latest_version_number__()

                if int(latest_version) - int(self.__build_version__) >= 5:
                    Utils.display_error_and_terminate(
                        f'The given version ({self.__build_version__}) is not available for download, '
                        f'oldest available: {int(latest_version) - 4}')
                if int(latest_version) < int(self.__build_version__):
                    Utils.display_error_and_terminate(f'The given version ({self.__build_version__}) does not exist')

            Utils.display_message(
                f'Downloading from: {self.__base_url__ + self.__download_url__} (it can take a few minutes)')
            apk = get(self.__base_url__ + self.__download_url__, verify=False)

            if apk.status_code != 200:
                if apk.status_code == 403:
                    Utils.display_error_and_terminate(
                        f'Download failed, possible reason is failed build, try another version')
                Utils.display_error_and_terminate(f'Download failed, response status: {apk.status_code}')

            Utils.display_message('Saving the downloaded file')
            open(self.file_url, 'wb').write(apk.content)

    def sign(self, file_path, pwd, name):
        if path.exists(self.file_url.replace('-unsigned', '')):
            Utils.display_message('apk is already signed')
            self.file_url = self.file_url.replace('-unsigned', '')
        else:
            try:
                Utils.display_message('Signing the apk (it can take a few minutes)')
                signing_status = str(check_output(['jarsigner', '-keystore', file_path,
                                                   '-storepass', pwd, self.file_url, name]))
                if 'jar signed.' in signing_status:
                    rename(self.file_url, self.file_url.replace('-unsigned', ''))
                    self.file_url = self.file_url.replace('-unsigned', '')
                    Utils.display_message('Signing successful')
                else:
                    remove(self.file_url)

                    Utils.display_error_and_terminate('Signing unsuccessful, removing file')
            except FileNotFoundError:
                Utils.display_error_and_terminate(
                    'jarsigner not found, please ensure that the latest JDK is installed and added to the system path')
            except CalledProcessError:
                Utils.display_error_and_terminate('Signing unsuccessful, please check the keystore details in the config file')


class Device:

    def __init__(self):
        self.__to_install__ = True
        self.__to_uninstall__ = True

    def check_connection(self):
        Utils.display_message('Checking connected device')
        try:
            devices_list_string = str(check_output(['adb', 'devices']))
            if len(devices_list_string.split('\\r')) < 4:
                Utils.display_message('There is no device connected, installation won\'t happen')
                self.__to_install__ = False
            elif len(devices_list_string.split('\\r')) > 4:
                Utils.display_error_and_terminate('There is more than one device connected')
        except FileNotFoundError:
            Utils.display_message('adb not found, installation won\'t happen')
            self.__to_install__ = False

    def check_space(self, required_space, app_name):
        if self.__to_install__:
            try:
                check_output(['adb', 'shell', 'cmd', 'package', 'path', app_name])
            except CalledProcessError:
                required_space = required_space * 2
                self.__to_uninstall__ = False
            try:
                Utils.display_message('Checking available space on device')
                device_space_string = check_output(['adb', 'shell', 'df'], encoding='ascii')
                storage = list(filter(lambda l: l.find('storage/emulated') != -1, device_space_string.splitlines()))
                if storage:
                    available_space = float(re.split(r'\s+', storage[0])[3])
                    if available_space / 1000000 < required_space:
                        Utils.display_error_and_terminate('There is not enough space on the device')
                else:
                    Utils.display_message('Could not check the available space, proceeding')
            except CalledProcessError:
                Utils.display_error_and_terminate('An error has occurred during device checking')

    def uninstall(self, app_name):
        if self.__to_uninstall__ and self.__to_install__:
            keep = input("Do you want the keep all user data? [Y/n] ")

            Utils.display_message('Uninstalling old version')

            if keep.lower() != 'n' and keep.lower() != 'no':
                uninstall_status = str(check_output(['adb', 'shell', 'cmd', 'package', 'uninstall', '-k', app_name]))
            else:
                uninstall_status = str(check_output(['adb', 'shell', 'cmd', 'package', 'uninstall', app_name]))

            if 'Success' in uninstall_status:
                Utils.display_message('Uninstall successful')
            else:
                Utils.display_error_and_terminate('Uninstall unsuccessful')

    def install(self, file_url, app_name):
        if self.__to_install__:
            try:
                Utils.display_message('Installing new version (it can take a few minutes)')
                install_status = str(check_output(['adb', 'install', file_url]))
                if 'Success' in install_status and check_output(['adb', 'shell', 'pm', 'list', 'packages', app_name]):
                    Utils.display_message('Install successful')
                else:
                    Utils.display_error_and_terminate('Install unsuccessful.\n'
                                          'Suggestions:\n'
                                          '   - try a different version\n'
                                          '   - try a fully uninstall and reinstall the current one')
            except CalledProcessError:
                Utils.display_error_and_terminate('Install unsuccessful')


def main():
    config = Config()
    device = Device()

    version = input("Version: [latest] ")
    krita = Krita(config.get("apk_config", "path"), version)

    device.check_connection()
    device.check_space(krita.required_space, krita.app_name)

    krita.download()
    krita.sign(config.get("keystore_config", "path"),
               config.get("keystore_config", "password"),
               config.get("keystore_config", "name"))

    device.uninstall(krita.app_name)
    device.install(krita.file_url, krita.app_name)

    Utils.display_message('Done!')
    input("Press Enter to exit...")


if __name__ == '__main__':
    main()
