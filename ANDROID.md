# Construir o APK WebView

O backend cria um projeto a partir de `android-template`. Para gerar APK num servidor:
1. Instale JDK 17.
2. Instale Android SDK Platform 35 e Build Tools 35.0.0.
3. Instale Gradle 8.9 e configure `ANDROID_HOME` ou `ANDROID_SDK_ROOT`.
4. Inicie a API com as permissões e isolamento apropriados.
5. Envie um ZIP que contenha `index.html` e seus arquivos CSS/JS/imagens.

O endpoint retorna um APK debug quando a ferramenta `gradle` e o SDK estão presentes. Para ambiente de produção, não execute builds de usuários sem container isolado, timeout, limites de CPU/memória e autenticação.
