# EtcherExplorer-vs-0.08
 Linux multi-tool software including GPU Acceleration, IDE Integration, CPU core control, and  much more

#Install depends:
sudo apt-get install pipenv python3-full python3-dev genisoimage ffmpeg ifupdown build-essential libssl-dev libffi-dev snapd cpufrequtils isc-dhcp-client dolphin ubuntu-drivers-common spyder nuitka libxcb-cursor0 pcscd gnome-screenshot smartmontools aidl sqlite3 libsqlite3-dev curl portaudio19-dev radeontop mesa-utils python3-gi gir1.2-vte-2.91 libglib2.0-dev libgirepository1.0-dev cmake gh git libcairo2-dev libvte-2.91-dev libgtk-3-dev p7zip-full gddrescue gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly xserver-xorg-video-radeon libx11-dev libxft-dev libfontconfig-dev dolphin

#Move project directory:
mv /current/dir ~/Etcher_Explorer

cd ~/Etcher_Explorer

# Configure virtual environment:
pipenv install
pipenv shell
pipenv run pip install PySide6 tk logging cryptography psutil py7zr screeninfo pydub Pillow opencv-python-headless requests beautifulsoup4 nuitka ffpyplayer xtarfile[zstd] pyinstaller matplotlib buildozer cython ttkbootstrap googlesearch-python ntplib nltk speechrecognition pyaudio scipy scikit-learn numpy PyGObject vte opencv-python send2trash openai python-gnupg keyring

# clone needed repositories:
gh repo clone aaryanrlondhe/Malware-Hash-Database

gh repo clone szTheory/exifcleaner

mv Malware-Hash-Database hashes

# Snap depends
sudo snap install alacritty --classic
sudo snap install drive-password

# Run the project by running command:
pipenv run python3 main.py


# Or you can create a .desktop item to make executable and move to ~/.local/share/applications Directory for easy access:
[Desktop Entry]
Name=Etcher Explorer Beta
Comment=Open Etcher Explorer main interface
Exec=bash -c "cd /home/usr/Etcher_Explorer && pipenv install && pipenv run python3 main2.py"
Icon=/home/usr/Etcher_Explorer/bico.ico
Type=Application
Terminal=False

# Simply change the /home/usr/Etcher_Explorer entries to have usr = your environments username in both places to make this .desktop file fully functional. To make put it in your apps launcher run:
cp /dirname/filename.desktop ~/.local/share/applicatons

# Enjoy and if anyone wants to collaborate I am always up for help.
