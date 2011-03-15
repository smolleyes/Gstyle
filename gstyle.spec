%define name gstyle
%define version 0.2
%define unmangled_version 0.2
%define release 1
%define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

Summary: Customise your gnome desktop and more
Name: %{name}
Version: %{version}
Release: %{release}
Source: http://files.penguincape.org/gstyle/releases/%{name}-%{unmangled_version}.tar.gz
License: GPLv2
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Laguillaumie sylvain <s.lagui@gmail.com>
Requires: python pygtk2 notify-python python-glade2 p7zip-full pygobject2 dbus-python wget python-metacity python-beautifulsoup xcur2png
Url: http://www.penguincape.org/
BuildRequires: python python-devel python-distutils-extra intltool sed

%description
Gstyle is a full gnome theme manager

Features:
* manage your gtk/icons/metacity/emerald/mouse/wallpapers
* create dynamic wallpapers
* manage your gdm settings and themes
* create and manage cubemodels themes for compiz
* create/download or export full customised themes 

%prep
%setup -q -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/gstyle/
%{_bindir}/gstyle
%doc %{_mandir}/man1/gstyle.1*
%{_datadir}/applications/gstyle.desktop
%{_datadir}/gstyle/
%{_datadir}/dbus-1/system-services/cn.gstyle.service
%{_sysconfdir}/dbus-1/system.d/cn.gstyle.conf
%{_datadir}/PolicyKit/policy/cn.gstyle.policy
%{_datadir}/polkit-1/actions/cn.gstyle.policy
%{_datadir}/locale/*/LC_MESSAGES/gstyle.mo
%{python_sitelib}/gstyle*.egg-info
%{_prefix}/share/pixmaps/puzzle.png

%changelog
* Sat 16 06 2010 Laguillaumie sylvain <s.lagui@gmail.com> 0.2
- Initial package
