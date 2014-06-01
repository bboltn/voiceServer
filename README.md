Let your voice be heard - server
-----------------------------------------------------------
## Rest end points and webapp


## Requirements

- Pip
- virtual env

## Install

```
git clone git@github.com:progrn/voiceServer.git
cd voiceServer
virtualenv .
source bin/activate
pip install -r requirements.txt
```

## Virtual Env Tips
- make source you have activated your pip virtualenv before coding OR running pip install
- to enter virtual env type `source bin/activate`
- to leave virtual env type `deactivate`
- if you install anything with pip install make sure you save these new requirements in requirements.txt.  Type `pip freeze > requirements.txt`


## REST End Points
```

http://api.kashew.net

/officials/USSenate/<zip>
/officials/USHouse/<zip>
/officials/Governor/<zip>
/officials/StateHouse/<zip>
/officials/StateSenate/<zip>
/officials/Local/<zip>
/candidate/<candidateId>

#you can also get multiple candidates by seperating ids with periods
/candidate/<candidateId.candidateId.candidateId.candidateId>
```
