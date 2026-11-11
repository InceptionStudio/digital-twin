import { Container, getContainer } from "@cloudflare/containers";

interface Env {
  BACKEND: DurableObjectNamespace<Backend>;

  // vars (wrangler.jsonc)
  JOB_STORAGE: string;
  MAX_FILE_SIZE_MB: string;
  FIRESTORE_COLLECTION: string;

  // secrets (wrangler secret put)
  FIRESTORE_PROJECT_ID: string;
  S3_BUCKET_NAME: string;
  AWS_REGION: string;
  OPENAI_API_KEY: string;
  ELEVENLABS_API_KEY: string;
  ELEVENLABS_API_TOKEN?: string;
  HEYGEN_API_KEY: string;
  AWS_ACCESS_KEY_ID: string;
  AWS_SECRET_ACCESS_KEY: string;
  GOOGLE_APPLICATION_CREDENTIALS_JSON: string;
}

export class Backend extends Container<Env> {
  defaultPort = 8000;

  // Jobs run as in-process background tasks and can wait up to 20 minutes on
  // HeyGen. Activity is only renewed by incoming requests, so keep the
  // container awake well past that even if the user stops polling.
  sleepAfter = "30m";

  enableInternet = true;

  // Production command. The Dockerfile's default CMD uses --reload, which is
  // for local development only.
  entrypoint = [
    "python",
    "-m",
    "uvicorn",
    "web_api:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--workers",
    "1",
  ];

  constructor(ctx: DurableObjectState<{}>, env: Env) {
    super(ctx, env);
    const vars: Record<string, string | undefined> = {
      JOB_STORAGE: env.JOB_STORAGE,
      MAX_FILE_SIZE_MB: env.MAX_FILE_SIZE_MB,
      FIRESTORE_PROJECT_ID: env.FIRESTORE_PROJECT_ID,
      FIRESTORE_COLLECTION: env.FIRESTORE_COLLECTION,
      S3_BUCKET_NAME: env.S3_BUCKET_NAME,
      AWS_REGION: env.AWS_REGION,
      OPENAI_API_KEY: env.OPENAI_API_KEY,
      ELEVENLABS_API_KEY: env.ELEVENLABS_API_KEY,
      ELEVENLABS_API_TOKEN: env.ELEVENLABS_API_TOKEN,
      HEYGEN_API_KEY: env.HEYGEN_API_KEY,
      AWS_ACCESS_KEY_ID: env.AWS_ACCESS_KEY_ID,
      AWS_SECRET_ACCESS_KEY: env.AWS_SECRET_ACCESS_KEY,
      GOOGLE_APPLICATION_CREDENTIALS_JSON: env.GOOGLE_APPLICATION_CREDENTIALS_JSON,
      WORKERS: "1",
      TEMP_DIR: "/app/temp",
      OUTPUT_DIR: "/app/output",
      PYTHONUNBUFFERED: "1",
    };
    // Drop unset optional values instead of passing empty strings.
    this.envVars = Object.fromEntries(
      Object.entries(vars).filter((e): e is [string, string] => !!e[1]),
    );
  }

  override onError(error: unknown) {
    console.error("Backend container error:", error);
    throw error;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Every request goes to the same named instance, so job polling, uploads
    // and downloads all reach the process that is running the job.
    return getContainer(env.BACKEND, "main").fetch(request);
  },
} satisfies ExportedHandler<Env>;
