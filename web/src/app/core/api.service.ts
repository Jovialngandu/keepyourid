import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CONFIG } from './config';
import { Credential, CredentialDraft, Issuance, Preparation } from '../shared/models';
@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = inject(CONFIG).apiBaseUrl.replace(/\/$/, '');
  private credentials(org: string) {
    return `${this.base}/organizations/${encodeURIComponent(org)}/credentials`;
  }
  health() {
    return this.http.get<{ status: string }>(`${this.base}/health`);
  }
  registerDid(
    org: string,
    data: { identifier: string; method: string; document: Record<string, unknown> },
  ) {
    return this.http.post<{ id: string; identifier: string }>(
      `${this.base}/dids/organizations/${encodeURIComponent(org)}`,
      data,
    );
  }
  challenge(did: string, domain: string) {
    return this.http.post<{ challenge_id: string; message: string; expires_at: string }>(
      `${this.base}/dids/${encodeURIComponent(did)}/challenges`,
      { purpose: 'did_authentication', domain },
    );
  }
  verifyDid(
    did: string,
    data: { challenge_id: string; verification_method: string; signature: string },
  ) {
    return this.http.post<{ identifier: string; status: string }>(
      `${this.base}/dids/${encodeURIComponent(did)}/verify`,
      data,
    );
  }
  register(data: {
    legal_name: string;
    registration_number: string;
    email: string;
    phone?: string;
  }) {
    return this.http.post<{ id: string; legal_name: string; status: string }>(
      `${this.base}/organizations/`,
      data,
    );
  }
  list(org: string) {
    return this.http.get<Credential[]>(this.credentials(org));
  }
  get(org: string, id: string) {
    return this.http.get<Credential>(`${this.credentials(org)}/${encodeURIComponent(id)}`);
  }
  create(org: string, data: CredentialDraft) {
    return this.http.post<Credential>(this.credentials(org), data);
  }
  prepare(org: string, id: string) {
    return this.http.post<Preparation>(
      `${this.credentials(org)}/${encodeURIComponent(id)}/prepare-issuance`,
      {},
    );
  }
  complete(org: string, id: string, data: { signature: string; key_id: string }) {
    return this.http.post<Issuance>(
      `${this.credentials(org)}/${encodeURIComponent(id)}/complete-issuance`,
      data,
    );
  }
}
