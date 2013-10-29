# lxcweb #

web interface of lxc(linux container)

# dependence #

* lxc (>= 0.9)
* python-webpy
* python-mako

* /etc/default/grub: cgroup_enable=memory
* bridge-utils
* setup br0
* setup net.ipv4.ip_forward = 1
* setup fstab for cgroup

    cgroup /sys/fs/cgroup cgroup defaults 0 2
