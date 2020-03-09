# Krita Android Downloader (and installer)
Makes it easier to download and install the latest nightly build of the Krita Android APK by automatising the whole workflow.\
The APK is only tested on a Samsung Galaxy Tab S3 using S Pen / STAEDTLER Noris digital (pressure sensitivity works perfectly with both of them) and a cheap bluetooth keyboard. The downloader is only tested on Windows 10. If you experience any issues on other platforms, please let me know.

## Before using Krita on android...
**Please keep in mind the followings:**
- the android version is in alpha state so it can have some glitches
- you will only be able to use it on an android tablet, the resolution is not suitable for phones at the moment
- you will need to have a keyboard connected to your tablet as the majority of the functions are only available using keyboard shortcuts at the moment 
- it requires around 3.2 GB free space on your internal storage to install; after it's installed, it will take up only around 1.6 GB

## Dependencies
###### Required dependencies:
- keystore is set up (this step is explained below)
- JDK (Java Development Kit) installed and added to your path (it includes keytool and jarsigner)
- internet connection
###### Optional dependencies:
- if you want to automatically install it on your tablet, you need to have ADB (part of Android SDK) installed and added to your path, and USB debugging enabled in the developer settings on your device
- if you don't want to use the exe (or use it on other OS than Windows), you need Python3 installed

## Usage
If you don't have a keystore set up, run the following in command line (remember to change the `mycustomname` and `mycustom_alias` to your keystore name and alias). It will also ask you some questions, the most important thing is the password, do remember what you type there, you will need it later.
```
keytool -genkey -v -keystore mycustomname.keystore -alias mycustom_alias -keyalg RSA -keysize 2048 -validity 10000
```
Fill the `krita.config` file correctly and place it in the same folder with your kad.exe/kad.py.\
**Example:**
```
[apk_config]
path = C:\Users\user_name\Documents\kad\apk\

[keystore_config]
path = C:\Users\user_name\Documents\kad\keystore\my-release-key.keystore
name = mycustom_alias
password = pwd
```
If you want to automatically install it on your tablet and all the requirements are fulfilled, you just need to connect your device via a USB cable to your PC.\
\
Then just run the script (or the exe on Windows). 
It will ask for the desired version, which means the build number. The default is the latest successful build.\
It will save the self-signed APK to the location specified in the config file.
You can now copy it to your tablet if you didn't do the automated installation. In this case you will also need to enable installation from foreign sources in the security settings.\
\
If you connected a device, it will also ask if you want to keep the user data before uninstalling the previous version (if you have any). The default value is yes.\
In this case if the app is nat installing, try again with not keeping the user data.\
\
If the app is not starting after installation, try with a different version.
