%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

%global modname fedmsg

Name:           python-fedmsg
Version:        0.1.2
Release:        1%{?dist}
Summary:        Tools for Fedora Infrastructure real-time messaging
Group:          Applications/Internet
License:        LGPLv2+
URL:            http://github.com/ralphbean/fedmsg
Source0:        http://pypi.python.org/packages/source/m/%{modname}/%{modname}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
BuildRequires:  moksha >= 0.8.0

Requires:       moksha >= 0.8.0
Requires:       python-fabulous
Requires:       python-simplejson
Requires:       python-zmq 


%description
Utilities used around Fedora Infrastructure to send and receive messages with
zeromq.  Includes:

 - A python API
 - A suite of CLI tools

%prep
%setup -q -n %{modname}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build \
    --install-data=%{_datadir} --root %{buildroot}

%{__mkdir_p} %{buildroot}%{_sysconfdir}
%{__cp} fedmsg-config.py %{buildroot}%{_sysconfdir}/fedmsg-config.py

%files 
%doc doc/ README.rst LICENSE
%{_bindir}/fedmsg-logger
%{_bindir}/fedmsg-status
%{_bindir}/fedmsg-tail
%{_bindir}/fedmsg-hub
%{_bindir}/fedmsg-relay
%{_bindir}/fedmsg-config
%{_bindir}/fedmsg-irc

%{python_sitelib}/%{modname}/
%{python_sitelib}/%{modname}-%{version}-py%{pyver}.egg-info/
%config(noreplace) %{_sysconfdir}/fedmsg-config.py*

%changelog
* Fri May 25 2012 Ralph Bean <rbean@redhat.com> - 0.1.2-1
-Version bump

* Wed May 02 2012 Ralph Bean <rbean@redhat.com> - 0.1.1-2
- Removed clean section
- Removed defattr in files section
- Removed unnecessary references to buildroot

* Thu Apr 26 2012 Ralph Bean <rbean@redhat.com> - 0.1.1-1
- Support for busmon websocket options.

* Sat Apr 14 2012 Ralph Bean <rbean@redhat.com> - 0.1.0-1
- Initial packaging.
