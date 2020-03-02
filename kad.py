from datetime import datetime
from requests import get
from os import path, remove, rename
from subprocess import check_output, CalledProcessError
import re
import configparser


class Console:

    @staticmethod
    def display_error(error_message):
        print(f'[{str(datetime.now()).split(".")[0]}]: Error - {error_message}')
        input("Press Enter to exit...")
        exit(1)

    @staticmethod
    def display_message(message):
        print(f'[{str(datetime.now()).split(".")[0]}]: {message}')


class Config:

    def __init__(self):
        if not path.exists('krita.config'):
            Console.display_error('\'krita.config\' does not exist')

        self.__config__ = configparser.RawConfigParser()
        self.__config__.read('krita.config')

    def get(self, config_name, valuse_name):
        return self.__config__.get(config_name, valuse_name)


class Krita:
    __base_url__ = "https://binary-factory.kde.org/job/Krita_Nightly_Android_Build/"

    app_name = 'org.krita'
    required_space = 1.5

    def __init__(self, file_path, version=''):
        if not version:
            Console.display_message('Checking new version')

            self.__build_version__ = 'undefined'

            res = get(self.__base_url__, verify=False)

            if res.status_code is not 200:
                Console.display_error(f'Version check failed, response statue: {res.status_code}')

            res = str(res.content).split("\\n")
            for item in res:
                if 'Last stable build' in item:
                    self.__build_version__ = item.split('(')[1].split(')')[0].replace('#', '')
                    Console.display_message(f'Latest version: {self.__build_version__}')
        else:
            self.__build_version__ = version

        if not file_path[-1] is '/' and file_path[-1] is not '\\':
            file_path += '/'

        self.file_url = f'{file_path}krita_build_apk-release-{self.__build_version__}-unsigned.apk'
        self.__download_url__ = f'{self.__build_version__}/artifact/krita_build_apk-release-unsigned.apk'

    def download(self):
        if path.exists(self.file_url) or path.exists(self.file_url.replace('-unsigned', '')):
            Console.display_message('The current version is already downloaded')
        else:
            Console.display_message(
                f'Downloading from: {self.__base_url__ + self.__download_url__} (it can take a few minutes)')
            apk = get(self.__base_url__ + self.__download_url__, verify=False)

            if apk.status_code is not 200:
                Console.display_error(f'Download failed, response status: {apk.status_code}')

            Console.display_message('Saving the downloaded file')
            open(self.file_url, 'wb').write(apk.content)

    def sign(self, file_path, pwd, name):
        if path.exists(self.file_url.replace('-unsigned', '')):
            Console.display_message('apk is already signed')
            self.file_url = self.file_url.replace('-unsigned', '')
        else:
            try:
                Console.display_message('Signing the apk (it can take a few minutes)')
                signing_status = str(check_output(['jarsigner', '-keystore', file_path,
                                                   '-storepass', pwd, self.file_url, name]))
                if 'jar signed.' in signing_status:
                    rename(self.file_url, self.file_url.replace('-unsigned', ''))
                    self.file_url = self.file_url.replace('-unsigned', '')
                    Console.display_message('Signing successful')
                else:
                    remove(self.file_url)

                    Console.display_error('Signing unsuccessful, removing file')
            except FileNotFoundError:
                Console.display_error(
                    'jarsigner not found, please ensure that the latest JDK is installed and added to the system path')
            except CalledProcessError:
                Console.display_error('Signing unsuccessful, please check the keystore details in the config file')


class Device:

    def __init__(self):
        self.__to_install__ = True
        self.__to_uninstall__ = True

    def check_connection(self):
        Console.display_message('Checking connected device')
        try:
            devices_list_string = str(check_output(['adb', 'devices']))
            if len(devices_list_string.split('\\r')) < 4:
                Console.display_message('There is no device connected, installation won\'t happen')
                self.__to_install__ = False
            elif len(devices_list_string.split('\\r')) > 4:
                Console.display_error('There is more than one device connected')
        except FileNotFoundError:
            Console.display_message('adb not found, installation won\'t happen')
            self.__to_install__ = False

    def check_space(self, required_space, app_name):
        if self.__to_install__:
            try:
                check_output(['adb', 'shell', 'cmd', 'package', 'path', app_name])
            except CalledProcessError:
                required_space = required_space * 2
                self.__to_uninstall__ = False
            try:
                Console.display_message('Checking available space on device')
                device_space_string = check_output(['adb', 'shell', 'df'], encoding='ascii')
                storage = list(filter(lambda l: l.find('storage/emulated') != -1, device_space_string.splitlines()))
                if storage:
                    available_space = float(re.split(r'\s+', storage[0])[3])
                    if available_space / 1000000 < required_space:
                        Console.display_error('There is not enough space on the device')
                else:
                    Console.display_message('Could not check the available space, proceeding')
            except CalledProcessError:
                Console.display_error('An error has occurred during device checking')

    def uninstall(self, app_name):
        if self.__to_uninstall__ and self.__to_install__:
            keep = input("Do you want the keep all user data? [Y/n] ")

            Console.display_message('Uninstalling old version')

            if keep.lower() is not 'n' and keep.lower() is not 'no':
                uninstall_status = str(check_output(['adb', 'shell', 'cmd', 'package', 'uninstall', '-k', app_name]))
            else:
                uninstall_status = str(check_output(['adb', 'shell', 'cmd', 'package', 'uninstall', app_name]))

            if 'Success' in uninstall_status:
                Console.display_message('Uninstall successful')
            else:
                Console.display_error('Uninstall unsuccessful')

    def install(self, file_url, app_name):
        if self.__to_install__:
            try:
                Console.display_message('Installing new version (it can take a few minutes)')
                install_status = str(check_output(['adb', 'install', file_url]))
                if 'Success' in install_status and check_output(['adb', 'shell', 'pm', 'list', 'packages', app_name]):
                    Console.display_message('Install successful')
                else:
                    Console.display_error('Install unsuccessful.\n'
                                          'Suggestions:\n'
                                          '   - try a different version\n'
                                          '   - try a fully uninstall and reinstall the current one')
            except CalledProcessError:
                Console.display_error('Install unsuccessful')


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

    Console.display_message('Done!')
    input("Press Enter to exit...")


if __name__ == '__main__':
    main()
