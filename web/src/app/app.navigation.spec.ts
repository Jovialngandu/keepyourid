import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { provideHttpClient } from '@angular/common/http';
import { CONFIG } from './core/config';
import { routes } from './app.routes';
describe('Navigation et rendu', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter(routes), provideHttpClient(), { provide: CONFIG, useValue: { apiBaseUrl: '/api/v1', workspaceEnabled: false } }] }));
  it('affiche l’accueil et navigue vers une page publique', async () => {
    const harness = await RouterTestingHarness.create('/');
    expect(harness.routeNativeElement?.textContent).toContain('Votre contrôle.');
    await harness.navigateByUrl('/organizations');
    expect(harness.routeNativeElement?.textContent).toContain('Donnez une nouvelle portée');
  });
  it('redirige les routes privées vers l’accès indisponible', async () => {
    const harness = await RouterTestingHarness.create('/issuer/credentials');
    expect(harness.routeNativeElement?.textContent).toContain('La connexion sera bientôt disponible.');
  });
  it('affiche une vraie page introuvable', async () => {
    const harness = await RouterTestingHarness.create('/page-inconnue');
    expect(harness.routeNativeElement?.textContent).toContain('Cette page est introuvable.');
  });
});
