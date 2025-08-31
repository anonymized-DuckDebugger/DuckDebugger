#!/bin/bash

# NOTE: this install script is b0rked. needs fixing.

SONARQUBE_ADMIN_PASS=admin1 # TODO - a modicum amount of secretsmanagement?

wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x ./dotnet-install.sh
./dotnet-install.sh --version latest
echo "export DOTNET_ROOT=$HOME/.dotnet" >> ~/.zshrc
echo "export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools" >> ~/.zshrc
echo "export DOTNET_ROOT=$HOME/.dotnet" >> ~/.bashrc
echo "export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools" >> ~/.bashrc
sudo ln -s ~/.dotnet/dotnet /usr/bin/dotnet

sudo mkdir -p /opt/sonar-everything && sudo chown $USER:$USER /opt/sonar-everything
cd /opt/sonar-everything
wget https://github.com/SonarSource/sonar-scanner-msbuild/releases/download/4.7.1.2311/sonar-scanner-msbuild-4.7.1.2311-netcoreapp2.0.zip
unzip sonar-scanner-msbuild-4.7.1.2311-netcoreapp2.0.zip
chmod +x /opt/sonar-everything/sonar-scanner-4.1.0.1829/bin/sonar-scanner
sudo ln -s `pwd`/sonar-scanner /usr/bin/sonar-scanner

dotnet tool install --global dotnet-sonarscanner --version 4.7.1
export PATH="$PATH:/home/$USER/.dotnet/tools"
echo 'export PATH="$PATH:/home/$USER/.dotnet/tools"' >> ~/.bash_profile


# Running sonarqube as a docker thing.
# Step ZERO: get docker.
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg jq -y
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# TODO: modify version string as needed
DOCKER_VERSION_STRING=5:24.0.7-1~debian.11~bullseye
sudo apt-get install -y \
docker-ce=$DOCKER_VERSION_STRING \
docker-ce-cli=$DOCKER_VERSION_STRING \
containerd.io \
docker-buildx-plugin \
docker-compose-plugin

# TODO: L52-56 give me pain on Debian Bullseye
if ! groups | grep docker; then
  sudo groupadd docker
fi
sudo usermod -aG docker $USER
newgrp docker # you'll still have to reboot eventually.
# --NOTE for (virtual) development environments:
# VMWare is not always playing nice with this stuff
# workaround: sudo service NetworkManager restart
#             adding 'nameserver 8.8.8.8' to /etc/resolv.conf

docker pull sonarqube:9.9.2-community
docker run -d --name sonarqube -p 9000:9000 -p 9092:9092 sonarqube:9.9.2-community

echo "Navigate to localhost:9000. Change password to 'admin1'"
echo "Go to: Administration -> Security -> Users- Click Tokens -> Generate Token"
echo -e "then do: \n \ 
  docker commit sonarqube sonartoken \n \
  docker stop -t0 sonarqube \n \
  docker run --rm -d --name sonart -p 9000:9000 sonartoken \n \
  export sonartoken=<WhateverTheDuckTokenYouGotInTheWebUI>"

# Let the monster awaken
# Check every n seconds (e.g., every 10 seconds)
echo -n "Waiting for SonarQube to become operational..."

while true; do
    # Get the last line of docker logs
    last_line=$(docker logs sonarqube | tail -n 1)

    # Check if the last line contains 'Web Server is operational'
    if echo "$last_line" | grep -qi "SonarQube is operational"; then
        echo "SonarQube is operational."
        break
    else
        # Wait for a bit before checking again
        sleep 10
        echo -n "."
    fi
done

# Additional sleep for 5 seconds
echo "Waiting an additional 5 seconds..."
sleep 5
echo "SonarQube should now be fully ready."

curl -X POST -u admin:admin "http://localhost:9000/api/users/change_password?login=admin&previousPassword=admin&password=$SONARQUBE_ADMIN_PASS"
response=`curl -X POST -u admin:$SONARQUBE_ADMIN_PASS "http://localhost:9000/api/user_tokens/generate?name=my_token"`
token=$(echo $response | jq -r '.token')

# Check if the token is not null or empty
if [ -n "$token" ] && [ "$token" != "null" ]; then
    # Export the token as an environment variable
    export SONAR_TOKEN=$token
    echo "export SONAR_TOKEN=$token" >> .bash_profile
    echo "export SONAR_TOKEN=$token" >> .bashrc
    echo "Token stored in SONAR_TOKEN environment variable."
else
    echo "Failed to retrieve token."
fi


# Automated attempt
mkdir -p /opt/sonar-everything/_TESTSITE
echo "sonar-project.properties
# must be unique in a given SonarQube instance
sonar.projectKey=testBed
sonar.token=$SONAR_TOKEN

# --- optional properties ---

sonar.scm.disabled=true

# defaults to project key
#sonar.projectName=My project
# defaults to 'not provided'
#sonar.projectVersion=1.0
 
# Path is relative to the sonar-project.properties file. Defaults to .
sonar.sources=.
sonar.language=c#
 
# Encoding of the source code. Default is default system encoding
sonar.sourceEncoding=UTF-8" >> /opt/sonar-everything/_TESTSITE/sonar-project.properties

# TODO: create basic testbed folder to dump c# in.
#         Requires: sonar-project.properties and SonarQube.Analysis.xml

# == sonar-project.properties ==

  #  sonar-project.properties
  #  # must be unique in a given SonarQube instance
  #  sonar.projectKey=test_1
  #  sonar.login=admin
  #  sonar.password=$SONARQUBE_ADMIN_PASS
  #  
  #  # --- optional properties ---
  #  
  #  sonar.scm.disabled=true
  #  
  #  # defaults to project key
  #  #sonar.projectName=My project
  #  # defaults to 'not provided'
  #  #sonar.projectVersion=1.0
  #   
  #  # Path is relative to the sonar-project.properties file. Defaults to .
  #  sonar.sources=.
  #  sonar.language=c#
  #   
  #  # Encoding of the source code. Default is default system encoding
  #  sonar.sourceEncoding=UTF-8

# == SonarQube.Analysis.xml ==

  #  <SonarQubeAnalysisProperties  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.sonarsource.com/msbuild/integration/2015/1">
  #      <Property Name="sonar.host.url">http://localhost:9000</Property>
  #      <Property Name="sonar.token">theSameDuckingToken</Property>
  #  </SonarQubeAnalysisProperties>
