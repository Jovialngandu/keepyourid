import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { CredentialDetail } from './credential-detail';
import { CONFIG } from '../../core/config';
import { WorkspaceService } from '../../core/workspace.service';
describe('Parcours d’émission', () => {
  it('requiert une confirmation et attend la réponse serveur avant de déclarer l’émission', () => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: CONFIG, useValue: { apiBaseUrl: '/api/v1', workspaceEnabled: true } },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: new Map([['id', 'credential']]) } },
        },
      ],
    });
    TestBed.inject(WorkspaceService).organizationId.set('organization');
    const fixture = TestBed.createComponent(CredentialDetail);
    const component = fixture.componentInstance;
    const http = TestBed.inject(HttpTestingController);
    http
      .expectOne('/api/v1/organizations/organization/credentials/credential')
      .flush({
        id: 'credential',
        credential_type: 'Diploma',
        status: 'DRAFT',
        credential_subject: {},
        payload: {},
        valid_from: '2026-01-01',
        valid_until: null,
      });
    component.prepare();
    http
      .expectOne('/api/v1/organizations/organization/credentials/credential/prepare-issuance')
      .flush({ signing_input: 'message', key_id: 'issuer#key' });
    component.form.setValue({ signature: 'external-signature' });
    component.requestConfirmation();
    expect(component.confirming()).toBe(true);
    expect(component.credential()?.status).toBe('DRAFT');
    component.complete();
    const request = http.expectOne(
      '/api/v1/organizations/organization/credentials/credential/complete-issuance',
    );
    expect(request.request.body).toEqual({ signature: 'external-signature', key_id: 'issuer#key' });
    expect(component.issuance()).toBeNull();
    request.flush({
      id: 'credential',
      credential_id: 'urn:uuid:credential',
      status: 'ISSUED',
      signed_credential: 'header.payload.signature',
    });
    expect(component.credential()?.status).toBe('ISSUED');
    expect(component.issuance()?.signed_credential).toBe('header.payload.signature');
    http.verify();
  });
});
