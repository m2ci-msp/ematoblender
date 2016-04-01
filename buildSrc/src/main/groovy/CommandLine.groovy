class CommandLine{

  // create windows friendly command line
  def osString(commandLine) {
    if(System.properties['os.name'].toLowerCase().contains('windows')){
      return "\"$commandLine\""
    }
    else{
      return commandLine
    }
  }

  def getOutput(path, arguments) {

    def process = "${osString(path)} $arguments".execute()
    def output = new ByteArrayOutputStream()
    def error = new ByteArrayOutputStream()

    process.consumeProcessOutput(output, error)
    process.waitForProcessOutput()

    def outputString = output.toString()
    if(outputString == "") {
      outputString = error.toString()
    }

    return outputString

  }

  def parseVersion(path, arguments, name) {

    def process = "${osString(path)} $arguments".execute()
    def output = new ByteArrayOutputStream()
    def error = new ByteArrayOutputStream()

    process.consumeProcessOutput(output, error)
    process.waitForProcessOutput()

    def outputString = output.toString()

    if(outputString == "") {
      outputString = error.toString()
    }

    return outputString.tokenize()[outputString.tokenize().findIndexOf{ it == name} + 1]

  }

}
