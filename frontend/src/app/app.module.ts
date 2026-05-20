import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';

import { AppComponent } from './app.component';
import { MapViewerComponent } from './components/map-viewer/map-viewer.component';
import { UploadComponent } from './components/upload/upload.component';
import { TaskStatusComponent } from './components/task-status/task-status.component';

@NgModule({
  declarations: [
    AppComponent,
    MapViewerComponent,
    UploadComponent,
    TaskStatusComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    StoreModule.forRoot({}, {}),
    EffectsModule.forRoot([]),
    StoreDevtoolsModule.instrument({ maxAge: 25 })
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
