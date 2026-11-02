import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { finalize, Subscription } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { WorkspaceService } from '../../core/workspace.service';
import { Credential } from '../../shared/models';
import { OrganizationContext } from '../../shared/organization-context';
@Component({
  imports: [OrganizationContext, RouterLink, DatePipe, FormsModule],
  templateUrl: './credential-list.html',
})
export class CredentialList {
  private api = inject(ApiService);
  private workspace = inject(WorkspaceService);
  private request?: Subscription;
  records = signal<Credential[]>([]);
  busy = signal(false);
  error = signal('');
  loaded = signal(false);
  query = signal('');
  status = signal('');
  page = signal(1);
  labels = { DRAFT: 'Brouillon', ISSUED: 'Émis', REVOKED: 'Révoqué' };
  drafts = computed(() => this.records().filter((c) => c.status === 'DRAFT').length);
  issued = computed(() => this.records().filter((c) => c.status === 'ISSUED').length);
  filtered = computed(() =>
    this.records().filter(
      (c) =>
        (!this.status() || c.status === this.status()) &&
        `${c.credential_type} ${c.credential_id}`
          .toLowerCase()
          .includes(this.query().toLowerCase()),
    ),
  );
  pages = computed(() => Math.max(1, Math.ceil(this.filtered().length / 10)));
  currentPage = computed(() => Math.min(this.page(), this.pages()));
  paginated = computed(() =>
    this.filtered().slice((this.currentPage() - 1) * 10, this.currentPage() * 10),
  );
  constructor() {
    if (this.workspace.organizationId()) this.load(this.workspace.organizationId());
  }
  load(id: string) {
    this.request?.unsubscribe();
    this.records.set([]);
    this.loaded.set(false);
    this.error.set('');
    this.busy.set(true);
    this.page.set(1);
    this.request = this.api
      .list(id)
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (r) => {
          this.records.set(r);
          this.loaded.set(true);
        },
        error: (e) => this.error.set(e.message),
      });
  }
  ngOnDestroy() {
    this.request?.unsubscribe();
  }
}
