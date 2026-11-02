import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { CONFIG } from '../../core/config';
import { Did } from './did';
describe('Preuve de contrôle DID', () => {
  it('lie la preuve au DID du challenge même si le formulaire est ensuite modifié', () => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: CONFIG, useValue: { apiBaseUrl: '/api/v1', workspaceEnabled: true } },
      ],
    });
    const component = TestBed.createComponent(Did).componentInstance;
    const http = TestBed.inject(HttpTestingController);
    const did = '11111111-1111-1111-1111-111111111111';
    component.authentication.setValue({ did, domain: 'keepyourid.local' });
    component.challenge();
    const request = http.expectOne(`/api/v1/dids/${did}/challenges`);
    expect(request.request.body).toEqual({
      purpose: 'did_authentication',
      domain: 'keepyourid.local',
    });
    request.flush({ challenge_id: 'challenge', message: 'message', expires_at: '2026-11-03' });
    component.authentication.controls.did.setValue('22222222-2222-2222-2222-222222222222');
    component.signature.setValue({ verification_method: 'did#controller', signature: '0x1234' });
    component.verify();
    const verification = http.expectOne(`/api/v1/dids/${did}/verify`);
    expect(verification.request.body.challenge_id).toBe('challenge');
    verification.flush({ identifier: 'did:ethr:sepolia:0x1234', status: 'VERIFIED' });
    expect(component.proof()).toBeNull();
    http.verify();
  });
});
