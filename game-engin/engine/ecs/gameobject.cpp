#include "ecs/gameobject.h"

namespace ge {

GameObject::GameObject(std::string name) : name_(std::move(name)) {}

GameObject::~GameObject() {
    DestroyComponents();
}

void GameObject::Destroy() {
    pending_destroy_ = true;
}

void GameObject::DestroyComponents() {
    for (Component* c : components_) {
        c->OnDestroy();
        delete c;
    }
    components_.clear();
}

}  // namespace ge
