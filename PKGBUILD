pkgname=bullseye-gtk-devel
pkgver=0.2
pkgrel=1
pkgdesc="A media/file manager that work by modules and display/sort files based on what they are instead of just where they are on the disk"
arch=('any')
url="http://daimao.info/bullseye"
license=('GPL2')
depends=('python2' 'pygtk' 'python-imaging' 'mutagen' 'gstreamer0.10-python' 'gstreamer0.10-good-plugins')

optdepends=('gstreamer0.10-bad-plugins: gstreamer backend support - formats'
	    'gstreamer0.10-ugly-plugins: gstreamer backend support - formats'
	    'gstreamer0.10-ffmpeg: gstreamer backend support - formats'
            'vlc: vlc backend support')

provides=('bullseye-gtk')

source=(https://launchpad.net/bullseye/trunk/30042012/+download/bullseye.tar.bz2)
install=$pkgname.install
md5sums=('f3633847977f4331cff9fe0fca218ded')


build() {

}

package() {
  cd "$srcdir/trunk"
  make DESTDIR="$pkgdir" install
}
