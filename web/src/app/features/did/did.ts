import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { WorkspaceService } from '../../core/workspace.service';
import { UUID_PATTERN } from '../../shared/organization-context';
import { parseSubject } from '../credentials/credential-create';
@Component({ imports: [ReactiveFormsModule], templateUrl: './did.html' })
export class Did {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  private workspace = inject(WorkspaceService);
  busy = signal(false);
  error = signal('');
  message = signal('');
  proof = signal<{ challenge_id: string; message: string; expires_at: string } | null>(null);
  private challengedDid = '';
  registration = this.fb.nonNullable.group({
    organization: [
      this.workspace.organizationId(),
      [Validators.required, Validators.pattern(UUID_PATTERN)],
    ],
    identifier: [
      '',
      [Validators.required, Validators.pattern(/^did:ethr:sepolia:0x[a-fA-F0-9]{40}$/)],
    ],
    document: ['', Validators.required],
  });
  authentication = this.fb.nonNullable.group({
    did: ['', [Validators.required, Validators.pattern(UUID_PATTERN)]],
    domain: ['keepyourid.local', [Validators.required, Validators.maxLength(255)]],
  });
  signature = this.fb.nonNullable.group({
    verification_method: ['', [Validators.required, Validators.maxLength(500)]],
    signature: ['', [Validators.required, Validators.pattern(/^0x[0-9a-fA-F]+$/)]],
  });
  register() {
    if (this.busy() || this.registration.invalid) return;
    const v = this.registration.getRawValue();
    let document: Record<string, unknown>;
    try {
      document = parseSubject(v.document);
    } catch {
      this.error.set('Le document DID doit être un objet JSON non vide.');
      return;
    }
    this.start();
    this.api
      .registerDid(v.organization, { identifier: v.identifier, method: 'ethr', document })
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (r) => {
          this.authentication.controls.did.setValue(r.id);
          this.message.set(`DID enregistré : ${r.id}`);
        },
        error: (e) => this.error.set(e.message),
      });
  }
  challenge() {
    if (this.busy() || this.authentication.invalid) return;
    const v = this.authentication.getRawValue();
    this.start();
    this.proof.set(null);
    this.api
      .challenge(v.did, v.domain.trim())
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (p) => {
          this.challengedDid = v.did;
          this.proof.set(p);
          this.signature.reset();
        },
        error: (e) => this.error.set(e.message),
      });
  }
  verify() {
    const p = this.proof();
    if (this.busy() || this.signature.invalid || !p) return;
    this.start();
    this.api
      .verifyDid(this.challengedDid, {
        challenge_id: p.challenge_id,
        ...this.signature.getRawValue(),
      })
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (r) => {
          this.message.set(`Contrôle confirmé par le serveur : ${r.identifier} (${r.status})`);
          this.proof.set(null);
          this.signature.reset();
        },
        error: (e) => this.error.set(e.message),
      });
  }
  private start() {
    this.error.set('');
    this.message.set('');
    this.busy.set(true);
  }
}
