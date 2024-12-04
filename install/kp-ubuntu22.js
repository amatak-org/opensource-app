#!/usr/bin/env node

const { spawn } = require('child_process');
const readline = require('readline');

const commands = [
  'sudo apt update',
  'sudo apt install -y nodejs',
  'sudo apt install -y npm',
  'sudo apt install -y python3',
  'sudo apt install -y python3-pip',
  'sudo pip install --upgrade psutil',
  'git clone https://github.com/amatak-org/opensource-app.git',
  'cd opensource-app',
  'python3 kpanel_install.py'
];

function runCommand(command) {
  return new Promise((resolve, reject) => {
    const process = spawn(command, [], { shell: true });

    process.stdout.on('data', (data) => {
      console.log(data.toString());
    });

    process.stderr.on('data', (data) => {
      console.error(data.toString());
    });

    const rl = readline.createInterface({
      input: process.stdout,
      output: process.stdout
    });

    rl.on('line', (input) => {
      if (input.toLowerCase().includes('do you want to continue?')) {
        process.stdin.write('y\n');
      }
    });

    process.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });
  });
}

async function runAllCommands() {
  for (const command of commands) {
    try {
      await runCommand(command);
      console.log(`Successfully executed: ${command}`);
    } catch (error) {
      console.error(`Error executing ${command}: ${error.message}`);
      process.exit(1);
    }
  }
}

runAllCommands();
