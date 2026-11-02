import { Injectable, signal } from '@angular/core';
@Injectable({ providedIn: 'root' })
export class WorkspaceService {
  // Memory only: no credentials or personal records persisted in browser storage.
  organizationId = signal('');
}
