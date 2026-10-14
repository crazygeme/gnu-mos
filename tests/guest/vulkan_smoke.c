/* Validate GPU submission and coherent host-visible memory through Vulkan. */
#include <vulkan/vulkan.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(expr) do { VkResult r = (expr); if (r != VK_SUCCESS) { \
    fprintf(stderr, "%s: %d\n", #expr, r); return 1; } } while (0)

int main(void)
{
    VkInstance instance;
    VkApplicationInfo app = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                             .apiVersion = VK_API_VERSION_1_1 };
    VkInstanceCreateInfo ici = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                                .pApplicationInfo = &app };
    CHECK(vkCreateInstance(&ici, NULL, &instance));
    uint32_t count = 0;
    CHECK(vkEnumeratePhysicalDevices(instance, &count, NULL));
    if (!count) return 2;
    VkPhysicalDevice *physical = calloc(count, sizeof(*physical));
    if (!physical) return 3;
    CHECK(vkEnumeratePhysicalDevices(instance, &count, physical));
    VkPhysicalDevice gpu = physical[0];
    free(physical);
    VkPhysicalDeviceProperties properties;
    vkGetPhysicalDeviceProperties(gpu, &properties);
    printf("GPU: %s; type=%u; API=%u.%u.%u\n", properties.deviceName,
           properties.deviceType, VK_VERSION_MAJOR(properties.apiVersion),
           VK_VERSION_MINOR(properties.apiVersion), VK_VERSION_PATCH(properties.apiVersion));
    fflush(stdout);
    if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_CPU) return 4;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, NULL);
    VkQueueFamilyProperties *families = calloc(count, sizeof(*families));
    if (!families) return 3;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, families);
    uint32_t family;
    for (family = 0; family < count; family++)
        if (families[family].queueFlags & VK_QUEUE_GRAPHICS_BIT) break;
    free(families);
    if (family == count) return 5;
    float priority = 1.0f;
    VkDeviceQueueCreateInfo qci = { .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = family, .queueCount = 1, .pQueuePriorities = &priority };
    VkDeviceCreateInfo dci = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                              .queueCreateInfoCount = 1, .pQueueCreateInfos = &qci };
    VkDevice device;
    CHECK(vkCreateDevice(gpu, &dci, NULL, &device));
    VkQueue queue;
    vkGetDeviceQueue(device, family, 0, &queue);
    VkBufferCreateInfo bci = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size = 4096, .usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT,
        .sharingMode = VK_SHARING_MODE_EXCLUSIVE };
    VkBuffer buffer;
    CHECK(vkCreateBuffer(device, &bci, NULL, &buffer));
    VkMemoryRequirements requirements;
    VkPhysicalDeviceMemoryProperties memory_properties;
    vkGetBufferMemoryRequirements(device, buffer, &requirements);
    vkGetPhysicalDeviceMemoryProperties(gpu, &memory_properties);
    uint32_t type;
    for (type = 0; type < memory_properties.memoryTypeCount; type++)
        if ((requirements.memoryTypeBits & (1U << type)) &&
            (memory_properties.memoryTypes[type].propertyFlags &
             (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
             (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) break;
    if (type == memory_properties.memoryTypeCount) return 6;
    VkMemoryAllocateInfo mai = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize = requirements.size, .memoryTypeIndex = type };
    VkDeviceMemory memory;
    CHECK(vkAllocateMemory(device, &mai, NULL, &memory));
    CHECK(vkBindBufferMemory(device, buffer, memory, 0));
    VkCommandPoolCreateInfo pci = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                   .queueFamilyIndex = family };
    VkCommandPool pool;
    CHECK(vkCreateCommandPool(device, &pci, NULL, &pool));
    VkCommandBufferAllocateInfo cai = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        .commandPool = pool, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1 };
    VkCommandBuffer command;
    CHECK(vkAllocateCommandBuffers(device, &cai, &command));
    VkCommandBufferBeginInfo cbi = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO };
    CHECK(vkBeginCommandBuffer(command, &cbi));
    vkCmdFillBuffer(command, buffer, 0, 4096, 0x1234abcd);
    VkMemoryBarrier barrier = { .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
        .srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT, .dstAccessMask = VK_ACCESS_HOST_READ_BIT };
    vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
                         0, 1, &barrier, 0, NULL, 0, NULL);
    CHECK(vkEndCommandBuffer(command));
    VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    VkFence fence;
    CHECK(vkCreateFence(device, &fci, NULL, &fence));
    VkSubmitInfo submit = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
        .commandBufferCount = 1, .pCommandBuffers = &command };
    CHECK(vkQueueSubmit(queue, 1, &submit, fence));
    CHECK(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL));
    uint32_t *mapped;
    CHECK(vkMapMemory(device, memory, 0, 4096, 0, (void **)&mapped));
    for (unsigned i = 0; i < 1024; i++)
        if (mapped[i] != 0x1234abcd) {
            fprintf(stderr, "GPU memory mismatch at %u: %08x\n", i, mapped[i]);
            return 7;
        }
    vkUnmapMemory(device, memory);
    CHECK(vkDeviceWaitIdle(device));
    vkDestroyFence(device, fence, NULL);
    vkDestroyCommandPool(device, pool, NULL);
    vkDestroyBuffer(device, buffer, NULL);
    vkFreeMemory(device, memory, NULL);
    vkDestroyDevice(device, NULL);
    vkDestroyInstance(instance, NULL);
    puts("GPU fill, fence completion, and host memory verification passed");
    return 0;
}
