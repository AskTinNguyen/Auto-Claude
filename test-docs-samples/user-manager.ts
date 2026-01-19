interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  isActive: boolean;
}

interface CreateUserParams {
  name: string;
  email: string;
}

class UserManager {
  private users: Map<string, User>;
  private nextId: number;

  constructor() {
    this.users = new Map();
    this.nextId = 1;
  }

  createUser(params: CreateUserParams): User {
    const user: User = {
      id: `user-${this.nextId++}`,
      name: params.name,
      email: params.email,
      createdAt: new Date(),
      isActive: true,
    };

    this.users.set(user.id, user);
    return user;
  }

  getUser(id: string): User | undefined {
    return this.users.get(id);
  }

  updateUser(id: string, updates: Partial<User>): User | null {
    const user = this.users.get(id);
    if (!user) {
      return null;
    }

    const updatedUser = { ...user, ...updates, id: user.id };
    this.users.set(id, updatedUser);
    return updatedUser;
  }

  deleteUser(id: string): boolean {
    return this.users.delete(id);
  }

  listUsers(activeOnly: boolean = false): User[] {
    const allUsers = Array.from(this.users.values());

    if (activeOnly) {
      return allUsers.filter(user => user.isActive);
    }

    return allUsers;
  }

  deactivateUser(id: string): boolean {
    const user = this.users.get(id);
    if (!user) {
      return false;
    }

    user.isActive = false;
    return true;
  }
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const formatUserName = (user: User): string => {
  return `${user.name} (${user.email})`;
};

export { User, CreateUserParams, UserManager, validateEmail, formatUserName };
