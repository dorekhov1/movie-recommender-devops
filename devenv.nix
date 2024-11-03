{ pkgs, ... }:

{
  packages = [ 
    pkgs.git 
    pkgs.ruff
    pkgs.python311Packages.debugpy
    pkgs.python311Packages.pytest
    pkgs.stdenv.cc.cc.lib
    pkgs.minikube
  ];

  languages.python = {
    enable = true;

    venv.enable = true;
    venv.requirements = ./requirements.txt;
  };
  dotenv.enable = true;
}
