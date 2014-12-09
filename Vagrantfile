# -*- mode: ruby -*-
# vi: set ft=ruby :

# Minimum required Vagrant version
Vagrant.require_version ">= 1.6.5"

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # INFO: https://vagrantcloud.com/hansode/boxes/centos-6.6-x86_64
  config.vm.box = "hansode/centos-6.6-x86_64"
  config.vm.network "public_network", bridge: 'en0: Wi-Fi (AirPort)'
  config.vm.synced_folder ".", "/opt/syco/"
  config.vm.provision :shell, path: "./bin/vagrant-provision"
  config.vm.post_up_message = "Syco sandbox installed"
end

