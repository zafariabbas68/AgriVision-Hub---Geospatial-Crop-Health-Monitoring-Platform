import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: `
    <div class="app-container">
      <header>
        <h1>🌾 AgriVision Hub</h1>
        <p>Drone-based Crop Health Monitoring</p>
      </header>
      
      <main>
        <div class="upload-section">
          <app-upload></app-upload>
        </div>
        
        <div class="map-section">
          <app-map-viewer></app-map-viewer>
        </div>
        
        <div class="status-section">
          <app-task-status></app-task-status>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      text-align: center;
    }
    main {
      display: grid;
      grid-template-columns: 1fr 2fr 1fr;
      gap: 20px;
      padding: 20px;
      height: calc(100vh - 120px);
    }
    .upload-section, .status-section {
      background: #f5f5f5;
      border-radius: 8px;
      padding: 20px;
      overflow-y: auto;
    }
    .map-section {
      background: #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
    }
    @media (max-width: 768px) {
      main {
        grid-template-columns: 1fr;
        grid-template-rows: auto 400px auto;
      }
    }
  `]
})
export class AppComponent {
  title = 'AgriVision Hub';
}
