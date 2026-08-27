#define MyAppName "Integracao EA-Khan"
#define MyAppVersion "1.0.1"

[Setup]
AppId={{7F31A8C1-5D84-4E21-BB3D-6A3F9C9E1D72}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}

AppPublisher=Gileno Mascarenhas
AppUpdatesURL=https://github.com/gilenomasc/integracao_ea_khan

VersionInfoDescription={#MyAppName}
VersionInfoCompany=Gi e Fe
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

WizardImageFile=..\assets\for_wizard_solid.bmp

DefaultDirName={localappdata}\Integracao_EA-Khan
PrivilegesRequired=lowest

CloseApplications=yes
RestartApplications=no

DisableWelcomePage=no

OutputBaseFilename=Setup_Integracao_EA_Khan_{#MyAppVersion}

SetupIconFile=..\assets\EA_Khan.ico
UninstallDisplayIcon={app}\app\unify_etapas.exe


[Files]
Source: "..\dist\integracao_ea_khan\*"; DestDir: "{app}\app"; Flags: recursesubdirs createallsubdirs

[Languages]

Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Dirs]
Name: "{app}\auth"
Name: "{app}\state"
Name: "{app}\dados"


[InstallDelete]
Type: filesandordirs; Name: "{app}\app"


[UninstallDelete]
Type: filesandordirs; Name: "{app}"


[Code]

var
  DirInfoLabel: TNewStaticText;

procedure InitializeWizard;
begin
  { Página de boas-vindas }

  WizardForm.WelcomeLabel1.Caption :=
    'Bem-vindo à instalação da Integração EA-Khan';

  WizardForm.WelcomeLabel2.Caption :=
    'Este assistente instalará os componentes necessários para a integração ' +
    'entre a Educação Adventista e a Khan Academy.' + #13#10 + #13#10 +
    'Após a instalação, os arquivos serão utilizados automaticamente pela ' +
    'planilha de integração.' + #13#10 + #13#10 +
    'Clique em "Avançar" para continuar.';


  { Página do diretório }

  WizardForm.SelectDirLabel.Caption :=
    'Selecione o local onde a Integração EA-Khan será instalada.';

  WizardForm.SelectDirBrowseLabel.Caption := '';


  { Explicação adicional }

  DirInfoLabel := TNewStaticText.Create(WizardForm);

  DirInfoLabel.Parent := WizardForm.SelectDirPage;

  DirInfoLabel.Caption :=
    'Para funcionamento correto da integração com o Excel, ' +
    'o diretório de instalação não pode ser alterado.';

  DirInfoLabel.AutoSize := False;
  DirInfoLabel.WordWrap := True;

  DirInfoLabel.SetBounds(
    WizardForm.SelectDirLabel.Left,
    WizardForm.SelectDirLabel.Top +
    WizardForm.SelectDirLabel.Height + 15,
    WizardForm.SelectDirPage.Width - WizardForm.SelectDirLabel.Left * 2,
    50
  );


  { Reposiciona os controles do diretório }

  WizardForm.DirEdit.Top :=
    DirInfoLabel.Top + DirInfoLabel.Height + 15;

  WizardForm.DirBrowseButton.Top :=
    WizardForm.DirEdit.Top;


  { Impede alteração do diretório }

  WizardForm.DirEdit.Enabled := False;
  WizardForm.DirBrowseButton.Enabled := False;

end;