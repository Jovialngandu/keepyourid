import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<a class="skip" href="#main">Aller au contenu</a><router-outlet />',
})
export class App {}
