# -*- mode: ruby -*-
# vi: set ft=ruby :

# Minimum required Vagrant version
Vagrant.require_version ">= 1.6.5"

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "mattiashem/syco_prep_centos6"
  config.vm.network "public_network", bridge: 'usb0: USB (dock)'
  config.vm.synced_folder ".", "/opt/syco/"
  config.vm.synced_folder ".", "/vagrant/"
  config.vm.provision :shell, path: "./bin/vagrant-provision"
  config.vm.post_up_message = "Syco sandbox installed"
  config.ssh.username="vagrant"
  config.ssh.password="vagrant"
end

