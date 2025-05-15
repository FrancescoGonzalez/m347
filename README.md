## Per runnare il container, eseguire:

```bash
docker build -t seb_vscode . && docker run -p 8080:8080 -v ./project:/home/coder/project -v ./config:/home/coder/.config -e PASSWORD=12345 -e EXTENSIONS_GALLERY=null seb_vscode
```