class CommandLine{

  def getOutput(commandLine) {

    def process = commandLine.execute()
    def output = new ByteArrayOutputStream()
    def error = new ByteArrayOutputStream()

    process.consumeProcessOutput(output, error)
    process.waitForProcessOutput()

    def outputString = output.toString()
    if(outputString == "") {
      outputString = error.toString()
    }

    return outputString.tokenize()[0]

  }

  def parseVersion(commandLine, name) {

    def process = commandLine.execute()
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
