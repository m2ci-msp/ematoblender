class CompareVersions{

  def isSmaller(a, b) {

    def (aMajor, aMinor) = a.split('.').take(2).collect{it.toInteger()}
    def (bMajor, bMinor) = b.split('.').take(2).collect{it.toInteger()}
      
    
    if (aMajor < bMajor){return true}
    if (aMajor == bMajor && aMinor < bMinor){return true}
    
    return false

  }

}
