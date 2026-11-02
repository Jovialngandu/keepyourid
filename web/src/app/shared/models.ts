export interface Credential {
  id: string;
  credential_id: string;
  organization_id: string;
  issuer_did_id: string;
  credential_type: string;
  credential_subject: Record<string, unknown>;
  payload: Record<string, unknown>;
  proof: Record<string, unknown> | null;
  status: 'DRAFT' | 'ISSUED' | 'REVOKED';
  valid_from: string;
  valid_until: string | null;
  created_at: string;
  updated_at: string;
}
export interface CredentialDraft {
  credential_type: string;
  subject: Record<string, unknown>;
  valid_until?: string;
}
export interface Preparation {
  signing_input: string;
  key_id: string;
}
export interface Issuance {
  id: string;
  credential_id: string;
  status: string;
  signed_credential: string;
}
