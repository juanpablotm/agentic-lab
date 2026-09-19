# Entorno de trabajo

Mac de Grupo Humano (Apple Silicon, macOS). Verificado el 5 de septiembre de 2026, D0.1.

## Versiones

| Herramienta | Version | Instalado con |
|-------------|---------|---------------|
| git | 2.50.1 (Apple Git-155) | Xcode CLT (hay tambien 2.55 de Homebrew, sin usar) |
| node | v26.8.1 | Homebrew |
| pnpm | 11.25.0 | Homebrew |
| gh | 2.100.0 | Homebrew |
| uv | 0.12.10 | instalador de Astral (`~/.local/bin`) |
| python | 3.12.14 | `uv python install 3.12` |

## La red del trabajo inspecciona TLS

**Sintoma:** cualquier cliente HTTPS que traiga su propio almacen de certificados
falla con `invalid peer certificate: UnknownIssuer`. Le paso a `uv` al intentar
descargar Python.

**Causa:** hay un proxy corporativo que termina la conexion TLS y la vuelve a firmar
con un certificado raiz de la empresa. Ese raiz esta en el llavero de macOS, asi que
todo lo que usa el almacen del sistema (Homebrew, curl, gh, git) funciona sin
problema. Lo que trae su propio almacen (uv con rustls, y probablemente httpx,
requests y npm) no lo conoce y rechaza la conexion.

**Arreglo general:** apuntar cada herramienta al almacen de certificados del sistema.

| Herramienta | Variable |
|-------------|----------|
| uv | `UV_SYSTEM_CERTS=1` (antes `UV_NATIVE_TLS`, ya deprecada) |
| requests | `REQUESTS_CA_BUNDLE=<ruta al pem>` |
| httpx / openssl / python en general | `SSL_CERT_FILE=<ruta al pem>` |
| node / npm / pnpm | `NODE_EXTRA_CA_CERTS=<ruta al pem>` |

Para exportar el certificado raiz corporativo a un `.pem` (pendiente, se resuelve
en D0.2 cuando httpx llame a las APIs de los proveedores):

```bash
security find-certificate -a -p /Library/Keychains/System.keychain > ~/.certs/corporativo.pem
```

**Por que anotar esto:** es friccion de entorno corporativo, no un problema mio ni de
la herramienta. En una aseguradora esto sale una y otra vez, y saber diagnosticarlo
en dos minutos en vez de en dos horas es parte del trabajo.


## Resolucion definitiva del TLS corporativo (D01, 19 sep 2026)

Las variables de entorno no bastan: cada libreria decide por su cuenta que almacen de
certificados usa.

| Libreria | Respeta | Resultado |
|---|---|---|
| `uv` | `UV_SYSTEM_CERTS=1` | funciona |
| `requests` (y por tanto `tiktoken`) | `REQUESTS_CA_BUNDLE` | funciona |
| `httpx` | **ninguna de las dos** — trae `certifi` fijado por dentro | fallaba |

La solucion que cubre todo a la vez es `truststore`, que hace que Python use el llavero
de macOS —donde ya esta el certificado raiz corporativo— en lugar de su propio paquete:

```bash
uv add truststore
```

```python
import truststore
truststore.inject_into_ssl()   # ANTES de importar httpx o cualquier SDK
```

Tiene que ir antes porque sustituye el mecanismo con el que Python construye sus contextos
TLS. Si la libreria ya se cargo con el suyo, llegas tarde.

Variables como respaldo, en `~/.zprofile`:

```
export UV_SYSTEM_CERTS=1
export SSL_CERT_FILE="$HOME/.certs/corporativo.pem"
export REQUESTS_CA_BUNDLE="$HOME/.certs/corporativo.pem"
```

El `.pem` se genera concatenando los dos llaveros —el del sistema, que tiene la raiz
corporativa, y el de raices publicas— porque el proxy no intercepta todo el trafico:

```bash
mkdir -p ~/.certs
security find-certificate -a -p /Library/Keychains/System.keychain > ~/.certs/corporativo.pem
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain >> ~/.certs/corporativo.pem
```

Ojo: un proceso lanzado desde el boton de ejecutar de VS Code **no hereda** los `export`
de una terminal. Por eso `truststore` es mejor que las variables: viaja dentro del codigo.
