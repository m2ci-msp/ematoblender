class CommandLine{

  // create windows friendly command line
  def osString(commandLine) {
    if(System.properties['os.name'].toLowerCase().contains('windows')){
      return "\"$gcommandLine\""
    }
    else{
      return commandLine
    }
  }

  def getOutput(commandLine) {

    def process = osString(commandLine).execute()
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

  def parseVersion(commandLine, name) {

    def process = osString(commandLine).execute()
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
