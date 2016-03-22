class CompareVersions{

  def isSmaller(a, b) {

    def aNumber = a.replace('.', '').toInteger()
    def bNumber = b.replace('.', '').toInteger()

    return aNumber < bNumber

  }

}
