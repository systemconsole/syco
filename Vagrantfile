# -*- mode: ruby -*-
# vi: set ft=ruby :

# Minimum required Vagrant version
Vagrant.require_version ">= 1.6.5"

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "centos/6"
  config.vm.network "public_network", bridge: 'EN0: WI-Fi (AirPort)'
  config.vm.synced_folder ".", "/opt/syco/", type: "virtualbox"
  config.vm.synced_folder ".", "/vagrant/", type: "virtualbox"
  config.vm.provision :shell, path: "./bin/vagrant-provision"
  config.vm.post_up_message = "Syco sandbox installed"
end

