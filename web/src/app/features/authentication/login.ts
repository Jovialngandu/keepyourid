import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CONFIG } from '../../core/config';
@Component({ imports: [RouterLink], templateUrl: './login.html' })
export class Login {
  config = inject(CONFIG);
}
