import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { CONFIG } from './config';
import { errorInterceptor } from './http-errors';
describe('API KeepYourID', () => {
  let api: ApiService;
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([errorInterceptor])),
        provideHttpClientTesting(),
        { provide: CONFIG, useValue: { apiBaseUrl: '/api/v1/', workspaceEnabled: false } },
      ],
    });
    api = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('respecte le contrat de création du backend', () => {
    const body = { credential_type: 'Diploma', subject: { id: 'did:example:holder' } };
    api.create('org', body).subscribe();
    const request = http.expectOne('/api/v1/organizations/org/credentials');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(body);
    request.flush({ id: 'draft' });
  });
  it('prépare puis finalise sans transmettre de clé privée', () => {
    api.prepare('org', 'credential').subscribe();
    const prepare = http.expectOne(
      '/api/v1/organizations/org/credentials/credential/prepare-issuance',
    );
    expect(prepare.request.method).toBe('POST');
    expect(prepare.request.body).toEqual({});
    prepare.flush({ signing_input: 'input', key_id: 'key' });
    api.complete('org', 'credential', { signature: 'signature', key_id: 'key' }).subscribe();
    const complete = http.expectOne(
      '/api/v1/organizations/org/credentials/credential/complete-issuance',
    );
    expect(complete.request.body).toEqual({ signature: 'signature', key_id: 'key' });
    complete.flush({ status: 'ISSUED' });
  });
  it('inscrit une organisation sur la route existante', () => {
    const body = {
      legal_name: 'Université',
      registration_number: '123',
      email: 'contact@example.org',
    };
    api.register(body).subscribe();
    const r = http.expectOne('/api/v1/organizations/');
    expect(r.request.body).toEqual(body);
    r.flush({ id: 'org' });
  });
  it('masque les traces serveur dans les erreurs', () => {
    let message = '';
    api.list('org').subscribe({ error: (e) => (message = e.message) });
    http
      .expectOne('/api/v1/organizations/org/credentials')
      .flush({ detail: 'private stack trace' }, { status: 500, statusText: 'Server Error' });
    expect(message).toBe('Une erreur est survenue sur le serveur.');
    expect(message).not.toContain('private');
  });
  it('préserve le contexte organisation pour la consultation', () => {
    api.get('first', 'second').subscribe();
    const r = http.expectOne('/api/v1/organizations/first/credentials/second');
    expect(r.request.method).toBe('GET');
    r.flush({ id: 'second' });
  });
});
