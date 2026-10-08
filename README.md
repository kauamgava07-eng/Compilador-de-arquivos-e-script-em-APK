# Script2APK — starter project

Script2APK é um protótipo mobile-first para preparar projetos para compilação Android.
**Esta primeira versão compila projetos HTML/CSS/JavaScript empacotados num APK Android WebView** e aceita projetos Android Gradle existentes como ponto de partida. Não promete converter qualquer script automaticamente: Python e projetos Godot precisam de runtimes/export templates próprios e ainda não têm adaptadores de compilação nesta versão.

## Conteúdo
- `web/`: interface web responsiva para selecionar e enviar um ZIP.
- `server/`: API FastAPI que valida uploads e cria um projeto Android WebView.
- `android-template/`: projeto Gradle mínimo usado como referência.
- `docs/`: instruções e limitações.
- `.github/workflows/`: workflow de verificação do projeto.

## Requisitos para compilar no servidor
- Linux
- Python 3.11+
- JDK 17
- Android SDK Platform 35 e Build Tools 35.0.0
- Gradle 8.9 (ou wrapper Gradle compatível)

## Executar a interface/API para desenvolvimento
```bash
cd server
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Abra `web/index.html` no navegador e informe a URL da API (por padrão `http://127.0.0.1:8000`). Em celular, `127.0.0.1` aponta para o próprio celular; para testar com servidor em outro computador, use o endereço IP desse computador. Para uso real, publique a API por HTTPS.

## Segurança
- Não publique esta API aberta na internet sem autenticação, limites de upload, quotas, isolamento de builds e limpeza automática.
- Não coloque tokens do GitHub, chaves de API ou senhas no JavaScript do navegador.
- Builds de arquivos enviados por terceiros devem rodar em containers isolados e sem segredos.
- O backend deste starter limita extensões e tamanho do upload, mas ainda é um protótipo e não é um serviço público pronto para produção.

## Formatos
| Entrada | Situação nesta versão |
|---|---|
| HTML/CSS/JS ZIP | Gera um projeto Android WebView e tenta compilar APK se o SDK estiver configurado |
| Projeto Android Gradle ZIP | Reconhece e valida estrutura básica; a compilação ainda requer execução controlada do Gradle no servidor |
| Python | Não converte automaticamente; precisa de estratégia/runtime específico |
| Godot/outros jogos | Requer export templates e configuração do projeto |
| ZIP genérico | Inspeciona estrutura e explica o próximo passo |

## APK assinado
O endpoint de protótipo gera APK debug. Para distribuição pública, configure assinatura de release e proteja a chave de assinatura fora do repositório.
