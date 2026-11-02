import { Component, inject, signal } from '@angular/core';
import { DatePipe, JsonPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { WorkspaceService } from '../../core/workspace.service';
import { Credential, Issuance, Preparation } from '../../shared/models';
import { OrganizationContext } from '../../shared/organization-context';
import { Confirmation } from '../../shared/confirmation';
@Component({
  imports: [DatePipe, JsonPipe, RouterLink, ReactiveFormsModule, OrganizationContext, Confirmation],
  templateUrl: './credential-detail.html',
})
export class CredentialDetail {
  private api = inject(ApiService);
  private workspace = inject(WorkspaceService);
  private id = inject(ActivatedRoute).snapshot.paramMap.get('id')!;
  private fb = inject(FormBuilder);
  credential = signal<Credential | null>(null);
  preparation = signal<Preparation | null>(null);
  issuance = signal<Issuance | null>(null);
  busy = signal(false);
  error = signal('');
  confirming = signal(false);
  form = this.fb.nonNullable.group({ signature: ['', Validators.required] });
  constructor() {
    if (this.workspace.organizationId()) this.load(this.workspace.organizationId());
  }
  load(org: string) {
    if (this.busy()) return;
    this.workspace.organizationId.set(org);
    this.credential.set(null);
    this.preparation.set(null);
    this.issuance.set(null);
    this.form.reset();
    this.error.set('');
    this.busy.set(true);
    this.api
      .get(org, this.id)
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({ next: (c) => this.credential.set(c), error: (e) => this.error.set(e.message) });
  }
  prepare() {
    if (this.busy()) return;
    this.error.set('');
    this.busy.set(true);
    this.preparation.set(null);
    this.api
      .prepare(this.workspace.organizationId(), this.id)
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (p) => {
          this.preparation.set(p);
          this.form.reset();
        },
        error: (e) => this.error.set(e.message),
      });
  }
  requestConfirmation() {
    if (this.form.valid && !this.busy() && this.preparation()) this.confirming.set(true);
  }
  complete() {
    this.confirming.set(false);
    const p = this.preparation();
    if (!p || this.busy() || this.form.invalid) return;
    this.error.set('');
    this.busy.set(true);
    this.api
      .complete(this.workspace.organizationId(), this.id, {
        signature: this.form.getRawValue().signature.trim(),
        key_id: p.key_id,
      })
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (r) => {
          this.issuance.set(r);
          this.credential.update((c) => (c ? { ...c, status: 'ISSUED' } : null));
          this.preparation.set(null);
          this.form.reset();
        },
        error: (e) => this.error.set(e.message),
      });
  }
  download() {
    const result = this.issuance();
    if (!result) return;
    const url = URL.createObjectURL(
      new Blob([result.signed_credential], { type: 'application/jose' }),
    );
    const link = document.createElement('a');
    link.href = url;
    link.download = `credential-${result.id}.jwt`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
