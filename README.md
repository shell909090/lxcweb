# lxcweb #

web interface of lxc(linux container)

# license #

This software is public under GPL-2+.

	This package is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.
	.
	This package is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	.
	You should have received a copy of the GNU General Public License
	along with this program. If not, see <http://www.gnu.org/licenses/>
	.
	On Debian systems, the complete text of the GNU General
	Public License version 2 can be found in "/usr/share/common-licenses/GPL-2".

# dependence #

* lxc (>= 0.9)
* python-webpy
* python-gevent

* /etc/default/grub: cgroup_enable=memory
* bridge-utils
* setup br0
* setup net.ipv4.ip_forward = 1
* setup fstab for cgroup

    cgroup /sys/fs/cgroup cgroup defaults 0 2
