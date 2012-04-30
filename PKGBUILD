pkgname=bullseye-qt-devel
pkgver=0.2
pkgrel=1
pkgdesc="A media/file manager that work by modules and display/sort files based on what they are instead of just where they are on the disk"
arch=('i686' 'x86_64')
url="http://daimao.info/bullseye"
license=('GPL2')
depends=('python2' 'pyside', 'python-imaging')

provides=('bullseye-qt')

source=(http://archive.xfce.org/src/xfce/$_pkgname/4.10/$_pkgname-$pkgver.tar.bz2)
md5sums=('4768e1a41a0287af6aad18b329a0f230')


build() {

}

package() {
  cd "$srcdir/$_pkgname-$pkgver"
  make DESTDIR="$pkgdir" install
}
