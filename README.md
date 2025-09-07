# 🎵 Finoboard

O **Finoboard** é um soundboard feito em **Python** com **PySide6**, **sounddevice** e **pydub**, com hotkeys globais, presets, múltiplos idiomas e build em **.exe** para Windows.

---

## ✨ Funcionalidades

- ✅ Adicionar arquivos de áudio (MP3, WAV, OGG, FLAC, M4A)  
- ✅ Interface em **Lista** ou **Grade** (com drag & drop)  
- ✅ **Hotkeys globais** configuráveis por áudio (sem duplicação)  
- ✅ **Presets** (áudios, hotkeys, volumes, dispositivos, idioma e layout)  
- ✅ **Mixer** com volume principal e **Monitor** (para ouvir local)  
- ✅ Idiomas: 🇧🇷 PT-BR, 🇺🇸 EN, 🇪🇸 ES, 🇯🇵 JA, 🇨🇳 ZH  
- ✅ Ícone do app embutido via **recursos do Qt** (estável na taskbar/Alt+Tab)  
- ✅ Builds **one-dir** (start rápido) e **one-file** (portável)

---

## 🖥️ Requisitos

- **Windows 10/11**  
- **Python 3.11+** (3.12/3.13 também funcionam)  
- **pip** atualizado  
- **FFmpeg (para desenvolvimento)** – recomendado via Chocolatey:
  ```powershell
  choco install ffmpeg
  ```
- **VB-CABLE** para roteamento de áudio virtual: https://vb-audio.com/Cable/

> Para o usuário final, o `.exe` pode incluir `ffmpeg/ffprobe`. Quem usa **VB-CABLE** deve instalar o driver.

---

## 🚀 Instalação (dev)

```powershell
git clone <URL_DO_REPO>
cd finoboard

python -m venv .venv
. .\.venv\Scripts\activate

pip install -r requirements.txt
```

### Recursos do Qt — ícone embutido (obrigatório)
O app usa `resources.qrc` → `resources_rc.py` para embutir o ícone. Gere o módulo (sempre que trocar o ícone):

```powershell
pyside6-rcc resources.qrc -o resources_rc.py
```

### Rodar em desenvolvimento

```powershell
python app.py
```

---

## 📂 Estrutura

```
app.py             # Janela principal (UI, presets, devices)
widgets.py         # Lista e grade (cards), tooltips, estilos
mixer.py           # Áudio (sounddevice/PortAudio)
audio_cache.py     # Decodificação (pydub/ffmpeg) + cache em memória
hotkeys.py         # Hotkeys globais (pynput) + deduplicação
i18n.py            # Traduções (PT, EN, ES, JA, ZH)
resources.qrc      # Recursos do Qt (ícone finoboard.ico)
resources_rc.py    # Gerado a partir do resources.qrc
requirements.txt   # Dependências
README.md          # Este arquivo
```

---

## ▶️ Como usar

1. **Dispositivos**  
   - Em **Saída**, escolha sua placa de som ou **CABLE Input (VB-Audio Virtual Cable)** para mandar o som para Discord, OBS ou qualquer outra aplicação.  
   - (Opcional) Em **Monitor**, selecione seus alto-falantes para ouvir localmente sem eco.

2. **Adicionar áudios**  
   - Clique em **Adicionar** ou arraste arquivos para a janela.  
   - Use **Lista** ou **Grade** (menu **Visualização**).

3. **Hotkeys**  
   - Em cada item, clique no ícone **⌨** e pressione a combinação desejada.  
   - Duplicatas são bloqueadas; o app avisa quais estão em uso.

4. **Volume & Mixer**  
   - Ajuste **Volume** geral e **Vol. monitor**.  
   - O **Mixer** mistura microfone + clipes para a saída principal; o **Monitor** toca só os clipes localmente.

5. **Presets**  
   - **Salvar preset…** e **Abrir preset…** guardam lista, hotkeys, volumes, dispositivos, idioma e layout.  
   - Ao abrir um preset, o app avisa caso algum arquivo esteja faltando e permite re-localizar.

---

## 🛠️ Build para Windows

Você pode gerar **one-dir** (pasta com DLLs, inicia mais rápido) ou **one-file** (um único `.exe`, mais portátil).

### Opção A — One-dir (recomendado para uso diário)
Início praticamente instantâneo:
```powershell
pyinstaller app.py `
  --name Finoboard `
  --noconsole `
  --onedir `
  --icon finoboard.ico
```
Saída: `dist\Finoboard\Finoboard.exe`

### Opção B — One-file (portável, pode iniciar mais lento)
Usando o **.spec** do projeto (inclui ícone do EXE, plugins mínimos do Qt e binários reais do ffmpeg/ffprobe quando habilitado):

```powershell
pyinstaller --noconfirm --clean finoboard.spec
```

#### Dicas de performance (one-file)
- Fixe o diretório de extração no `.spec` (campo `runtime_tmpdir`) e faça **whitelist no antivírus**.  
- Se notar lentidão com **UPX**, desative `upx=True` no `.spec` (ou use `--noupx`).  
- Para reduzir extração e peso, **não** empacote `ffmpeg/ffprobe` e instale via Chocolatey no PC do usuário.

---

## 🐛 Solução de problemas

- **Start do .exe está lento (one-file)**  
  - Prefira **one-dir** para uso diário, ou  
  - Defina `runtime_tmpdir` no `.spec` e faça whitelist no AV, e/ou  
  - Desative **UPX** no `.spec`.

- **FFmpeg não encontrado (dev)**  
  - Instale via Chocolatey ou coloque `ffmpeg/ffprobe` no `PATH`.

---

## 🤝 Contribuindo

1. Abra uma issue descrevendo bug/feature.  
2. Crie um branch (`feat/...` ou `fix/...`).  
3. Faça commits claros (ex.: `feat(ui): melhorar destaque de hotkeys`).  
4. Abra PR vinculando à issue.

---

## ⚖️ Licenças

- Este projeto usa bibliotecas de terceiros (Qt/PySide6, sounddevice, pydub, numpy, pynput).  
- **FFmpeg** pode ser redistribuído conforme a licença do pacote utilizado.  
- Consulte os arquivos/licenças correspondentes.
