# ESTADO_SGEJ.md — Punto de Control del Proyecto

## Última actualización: 2026-07-01

## Resumen General

Proyecto SGEJ (Sistema de Gestor de Expedientes Jurídicos).
Monolito modular Django 5.2 + DRF + MySQL 8.0 + Bootstrap 5.
5 apps domain-driven: usuarios, expedientes, documentos, biblioteca, infraestructura.

## Estado por Módulo

| Módulo | Estado | Observaciones |
|---|---|---|
| `usuarios/` | ✅ Completo | 3 roles (ADMIN, ABOG, USR_PUBLICO), RBAC en vistas, 2FA. |
| `expedientes/` | ✅ Completo | 11 modelos, 20+ vistas, API REST, exportación Excel. |
| `documentos/` | ✅ Completo | Cifrado Fernet, QR, firmas, hash verification, watermark PDF. |
| `biblioteca/` | ✅ Completo | CRUD + API REST wiredeada. Sin tests. |
| `infraestructura/` | ✅ Completo | RateLimit, SessionControl, Auditoría Inmutable con honeypot. |
| `sgej_config/` | ✅ Completo | Settings, urls, wsgi, asgi listos. |
| `templates/` | ✅ Completo | 44 templates. Creados errors/404.html y errors/500.html. |
| `static/` | ✅ Completo | CSS (803 líneas), JS (3 módulos), imágenes. |

## Tareas Completadas

- [x] `.gitignore` creado (24 reglas)
- [x] Fix doble conteo de intentos fallidos
- [x] Fix formularios (form-control, historial único, _password_plana_temporal)
- [x] Roles reducidos: ADMIN, ABOG, USR_PUBLICO
- [x] Migraciones aplicadas
- [x] `RoleRequiredMixin` + RBAC en vistas de usuarios
- [x] ABOG no puede crear/editar ADMIN
- [x] Sidebar actualizado con nuevos roles
- [x] Username corregido: `leonardo`
- [x] Hash verification al descargar documentos
- [x] Marca de agua dinámica en PDFs (cédula + fecha + nombre)
- [x] Página 404 personalizada
- [x] Página 500 personalizada
- [x] API de biblioteca creada y wiredeada
- [x] `qr_code_content` max_length corregido (500→255)
- [x] `pypdf` + `reportlab` agregados a requirements.txt

## Pendientes

Ninguno — Sprint completado.

## Sprint 2026-07-01 (tarde)

- [x] **Fichero de Sujetos Procesales**: Nuevo modelo `SujetoProcesal` con tipos parametrizados: Defensor (DEF), Fiscal de Control (FIS), Juez de la Causa (JUE), Secretario Judicial (SEC), Contraparte (CON). CRUD completo, exportación Excel, API REST, sidebar. Tabla `sujetos_procesales`.
- [x] **Expediente vinculado**: Campos `defensor`, `fiscal`, `juez`, `secretario` como FK opcionales a `SujetoProcesal` en el modelo `Expediente`.

## Sprint 2026-07-01 (mañana)

- [x] **Bug fix**: `ExportarBibliotecaExcelView` corregido — pasaba argumentos incorrectos al servicio de exportación
- [x] **Tests**: Creados tests completos para `apps/biblioteca` (17 tests: modelos, vistas, filtros, exportación)
- [x] **Generación automática de documentos**: CRUD completo de plantillas (`/documentos/plantillas/`) + generación con reemplazo de variables {{...}} desde archivos .docx. Cifrado automático al generar.
- [x] **Service Worker**: `static/js/sw.js` registrado en `base.html`. Cachea assets estáticos y responde con fallback offline para API requests.
- [x] **SessionControlMiddleware**: Separado en `CACHES['session_control']` para facilitar migración futura a `DatabaseCache`/`RedisCache` en producción multi-worker. En desarrollo usa `LocMemCache`.

## Credenciales

```
Usuario:  leonardo
Password: Admin.2026!!
Rol:      ADMIN
```

## Instrucciones de Recuperación

Si la conexión se pierde:
1. Leer este archivo (`ESTADO_SGEJ.md`)
2. Buscar la tarea pendiente más arriba
3. Continuar desde allí
