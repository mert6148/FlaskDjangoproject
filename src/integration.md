# CS-Script VSCode extension integration

Detected CS-Script tools:

- Script engine: `C:\Users\mertd\.dotnet\tools\.store\cs-script.cli\4.12.0.1\cs-script.cli\4.12.0.1\tools\net10.0\any\cscs.dll`
- Syntaxer: `C:\Users\mertd\.dotnet\tools\.store\cs-syntaxer\3.2.6\cs-syntaxer\3.2.6\tools\net10.0\any\syntaxer.dll`

The extension settings have been updated.
You may need to restart VSCode for the changes to take effect

---------------

You can always update (or install) CS-Script tools:

- Script engine: `dotnet tool update --global cs-script.cli`
- Syntaxer: `dotnet tool update --global cs-syntaxer`

If you cannot update because script engine or syntaxer executables are locked, you can always terminate any running instance with:
  `css -kill`
  `syntaxer -kill`

Configure tools by executing the extension command "CS-Script: Integrate with CS-Script tools"

---------------

You can always check the version of the CS-SCript tools from the terminal by executing the command:
Script engine: `css`
Syntaxer: `syntaxer`
