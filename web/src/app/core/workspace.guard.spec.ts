import { TestBed } from '@angular/core/testing';
import {
  provideRouter,
  Router,
  UrlTree,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
} from '@angular/router';
import { CONFIG } from './config';
import { workspaceGuard } from './workspace.guard';
describe('Accès au portail local', () => {
  function run(enabled: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: CONFIG, useValue: { apiBaseUrl: '/api/v1', workspaceEnabled: enabled } },
      ],
    });
    return TestBed.runInInjectionContext(() =>
      workspaceGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );
  }
  it('ferme le portail par défaut', () => {
    const result = run(false);
    expect(result instanceof UrlTree).toBe(true);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/login');
  });
  it('ouvre uniquement le mode explicitement configuré', () => expect(run(true)).toBe(true));
});
