import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';
import { CONFIG, RuntimeConfig } from './app/core/config';
async function bootstrap() {
  const response = await fetch('/config.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('Configuration indisponible');
  const config: RuntimeConfig = await response.json();
  if (
    !config.apiBaseUrl ||
    !/^\/(?!\/)|^https?:\/\//.test(config.apiBaseUrl) ||
    typeof config.workspaceEnabled !== 'boolean'
  )
    throw new Error('Configuration invalide');
  await bootstrapApplication(App, {
    ...appConfig,
    providers: [...appConfig.providers, { provide: CONFIG, useValue: config }],
  });
}
bootstrap().catch(() => {
  document.body.textContent =
    'KeepYourID ne peut pas démarrer. Vérifiez la configuration de l’application.';
});
